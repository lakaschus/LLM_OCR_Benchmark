import os
from datasets import load_dataset, Dataset, Features, Sequence, Value, ClassLabel, DatasetDict
from PIL import Image

def load_image(image_path):
    return Image.open(image_path).convert("RGB")

class CustomFUNSD:
    def __init__(self, data_dir, split):
        self.data_dir = data_dir
        self.split = split
        self.ann_dir = os.path.join(data_dir, f"{split}_data/annotations")
        self.img_dir = os.path.join(data_dir, f"{split}_data/images")
        self.files = sorted(os.listdir(self.ann_dir))
        
    def __len__(self):
        return len(self.files)
    
    def __iter__(self):
        for idx, file in enumerate(self.files):
            ann_path = os.path.join(self.ann_dir, file)
            img_path = os.path.join(self.img_dir, file.replace("json", "png"))
            
            with open(ann_path, "r", encoding="utf8") as f:
                annotation = json.load(f)
            
            tokens, bboxes, ner_tags = [], [], []
            for item in annotation["form"]:
                words, label = item["words"], item["label"]
                words = [w for w in words if w["text"].strip() != ""]
                if len(words) == 0:
                    continue
                if label == "other":
                    for w in words:
                        tokens.append(w["text"])
                        ner_tags.append("O")
                        bboxes.append(w["box"])
                else:
                    tokens.append(words[0]["text"])
                    ner_tags.append("B-" + label.upper())
                    bboxes.append(words[0]["box"])
                    for w in words[1:]:
                        tokens.append(w["text"])
                        ner_tags.append("I-" + label.upper())
                        bboxes.append(w["box"])
            
            yield {
                "id": str(idx),
                "tokens": tokens,
                "bboxes": bboxes,
                "ner_tags": ner_tags,
                "image_path": img_path
            }
def get_features():
    return Features({
        "id": Value("string"),
        "tokens": Sequence(Value("string")),
        "bboxes": Sequence(Sequence(Value("int64"))),
        "ner_tags": Sequence(ClassLabel(names=[
            "O", "B-HEADER", "I-HEADER", "B-QUESTION", "I-QUESTION", "B-ANSWER", "I-ANSWER"
        ])),
        "image_path": Value("string"),
    })

def load_funsd_dataset(data_dir):
    train_dataset = Dataset.from_generator(
        lambda: CustomFUNSD(data_dir, "training"),
        features=get_features()
    )
    test_dataset = Dataset.from_generator(
        lambda: CustomFUNSD(data_dir, "testing"),
        features=get_features()
    )
    return DatasetDict({"train": train_dataset, "test": test_dataset})

# Usage example
if __name__ == "__main__":
    import json
    
    # Specify the path to your FUNSD dataset directory
    funsd_dir = "dataset/"
    
    dataset = load_funsd_dataset(funsd_dir)
    # Save the dataset to disk
    output_dir = "dataset/prepared/"
    dataset.save_to_disk(output_dir)
    print(f"Dataset saved to {output_dir}")
    
    # Get the first example from the training set
    example = dataset['train'][0]
    
    # Print some information
    print("Tokens:", example['tokens'][:10])  # Print first 10 tokens
    print("NER tags:", example['ner_tags'][:10])  # Print first 10 NER tags
