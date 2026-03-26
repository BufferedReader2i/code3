"""
DistilBERT 新闻文本分类训练脚本
- 保留所有类别，过采样补足极少类
- 类别加权 CrossEntropyLoss 处理不均衡
- 标题 + 摘要双段输入
- 分层学习率 + warmup + 余弦衰减
- 早停（宏平均 F1）+ 保存最佳模型
"""
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import f1_score
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    get_cosine_schedule_with_warmup,
)

# ---------- 超参数 ----------
DATA_PATH       = 'datal/news.tsv'
SAVE_PATH       = 'distilbert_news.pth'
MODEL_NAME      = 'distilbert-base-uncased'
MAX_LEN         = 128
BATCH_SIZE      = 32
EPOCHS          = 10
LR_BERT         = 2e-5   # DistilBERT 层学习率
LR_HEAD         = 1e-4   # 分类头学习率
WARMUP_RATIO    = 0.1    # 前 10% step 做 warmup
OVERSAMPLE_MIN  = 50     # 少于此条数的类别过采样到此数量
EARLY_STOP      = 3      # 宏 F1 连续不提升轮数
SEED            = 42

# ---------- 固定随机种子 ----------
def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# ---------- 加载数据 ----------
def load_news(path=DATA_PATH):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"数据文件不存在: {path}")
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                rows.append({
                    'category': parts[1],
                    'title':    parts[3],
                    'abstract': parts[4],
                })
    return pd.DataFrame(rows).dropna()

# ---------- 过采样：保留所有类别 ----------
def oversample(df, min_count=OVERSAMPLE_MIN):
    parts = []
    for cat, group in df.groupby('category'):
        if len(group) < min_count:
            # 重复采样补足
            group = group.sample(min_count, replace=True, random_state=SEED)
        parts.append(group)
    return pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)

# ---------- Dataset ----------
class NewsDataset(Dataset):
    def __init__(self, titles, abstracts, labels, tokenizer):
        # 标题和摘要分开传，tokenizer 自动插入 [SEP]
        enc = tokenizer(
            list(titles),
            list(abstracts),
            truncation=True,
            padding='max_length',
            max_length=MAX_LEN,
            return_tensors='pt',
        )
        self.input_ids      = enc['input_ids']
        self.attention_mask = enc['attention_mask']
        self.labels         = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, i):
        return self.input_ids[i], self.attention_mask[i], self.labels[i]

# ---------- 主流程 ----------
def main():
    set_seed()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"设备: {device}")

    # 1. 加载 & 过采样
    df = load_news()
    print(f"原始数据: {len(df)} 条，{df['category'].nunique()} 类")
    df = oversample(df)
    print(f"过采样后: {len(df)} 条")

    # 2. 编码类别
    le = LabelEncoder()
    df['label'] = le.fit_transform(df['category'])
    num_classes = len(le.classes_)
    print(f"类别数: {num_classes} → {list(le.classes_)}")

    # 3. 划分训练 / 验证集（按类别分层）
    train_df, val_df = train_test_split(
        df, test_size=0.2, random_state=SEED, stratify=df['label']
    )
    print(f"训练: {len(train_df)}  验证: {len(val_df)}")

    # 4. Tokenizer
    print("加载 Tokenizer...")
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)
    # 保存 tokenizer，便于 demo 完全离线加载（不依赖在线下载/缓存）
    try:
        tokenizer.save_pretrained("distilbert_tokenizer")
    except Exception:
        pass

    train_ds = NewsDataset(train_df['title'].tolist(), train_df['abstract'].tolist(),
                           train_df['label'].tolist(), tokenizer)
    val_ds   = NewsDataset(val_df['title'].tolist(),   val_df['abstract'].tolist(),
                           val_df['label'].tolist(),   tokenizer)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE)

    # 5. 类别权重（处理不均衡）
    class_weights = compute_class_weight(
        'balanced', classes=np.arange(num_classes), y=train_df['label'].values
    )
    criterion = nn.CrossEntropyLoss(
        weight=torch.tensor(class_weights, dtype=torch.float).to(device)
    )

    # 6. 模型
    print("加载 DistilBERT...")
    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=num_classes
    ).to(device)

    # 7. 分层学习率：BERT 层用小 lr，分类头用大 lr
    optimizer = torch.optim.AdamW([
        {'params': model.distilbert.parameters(), 'lr': LR_BERT},
        {'params': model.classifier.parameters(), 'lr': LR_HEAD},
        {'params': model.pre_classifier.parameters(), 'lr': LR_HEAD},
    ], weight_decay=0.01)

    total_steps   = len(train_loader) * EPOCHS
    warmup_steps  = int(total_steps * WARMUP_RATIO)
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    # 8. 训练循环
    best_f1       = 0.0
    no_improve    = 0

    for epoch in range(EPOCHS):
        # --- 训练 ---
        model.train()
        total_loss = 0
        for step, (input_ids, attn_mask, labels) in enumerate(train_loader):
            input_ids = input_ids.to(device)
            attn_mask = attn_mask.to(device)
            labels    = labels.to(device)

            outputs = model(input_ids=input_ids, attention_mask=attn_mask)
            loss    = criterion(outputs.logits, labels)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()
            if (step + 1) % 50 == 0:
                print(f"  [Epoch {epoch+1}] step {step+1}/{len(train_loader)}  loss={loss.item():.4f}")

        avg_loss = total_loss / len(train_loader)

        # --- 验证 ---
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for input_ids, attn_mask, labels in val_loader:
                input_ids = input_ids.to(device)
                attn_mask = attn_mask.to(device)
                logits    = model(input_ids=input_ids, attention_mask=attn_mask).logits
                preds     = logits.argmax(dim=-1).cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(labels.numpy())

        val_acc = 100 * np.mean(np.array(all_preds) == np.array(all_labels))
        val_f1  = f1_score(all_labels, all_preds, average='macro') * 100
        print(f"✓ Epoch {epoch+1}/{EPOCHS} | loss={avg_loss:.4f} | acc={val_acc:.2f}% | macro-F1={val_f1:.2f}%")

        # --- 保存最佳 & 早停 ---
        if val_f1 > best_f1:
            best_f1    = val_f1
            no_improve = 0
            torch.save({
                'model':         model.state_dict(),
                'label_encoder': le,
                'label_classes': list(le.classes_),
                'model_name':    MODEL_NAME,
                'num_classes':   num_classes,
                'tokenizer_path': "distilbert_tokenizer",
            }, SAVE_PATH)
            print(f"  → 最佳模型已保存 (macro-F1={best_f1:.2f}%)\n")
        else:
            no_improve += 1
            if no_improve >= EARLY_STOP:
                print(f"早停：macro-F1 连续 {EARLY_STOP} 轮未提升，训练结束。")
                break

    print(f"\n训练结束，最佳 macro-F1: {best_f1:.2f}%，模型保存至 {SAVE_PATH}")

if __name__ == '__main__':
    main()
