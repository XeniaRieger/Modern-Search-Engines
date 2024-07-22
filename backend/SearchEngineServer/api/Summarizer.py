from transformers import BartTokenizer, BartForConditionalGeneration
from tqdm import tqdm
import torch

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
model = model.to(device)
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
MAX_SUMMARY_LEN = 300

def generate_batch_summary(docs):
    for d in tqdm(docs):
        text = d['raw_text'].strip()
        if len(text) > MAX_SUMMARY_LEN:
            d['summary'] = generate_summary(text)

def generate_summary(doc_text):
    inputs = tokenizer.encode(doc_text, return_tensors="pt", max_length=1024, truncation=True).to(device)
    summary_ids = model.generate(inputs, max_length=MAX_SUMMARY_LEN, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary
