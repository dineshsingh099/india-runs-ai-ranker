import os
import sys

def download():
    model_name = "all-MiniLM-L6-v2"
    save_path = os.path.abspath("./models/all-MiniLM-L6-v2")
    
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Error: sentence-transformers package not installed. Run pip install sentence-transformers first.")
        sys.exit(1)
        
    print(f"Downloading model '{model_name}' from Hugging Face...")
    model = SentenceTransformer(model_name)
    
    print(f"Saving model to '{save_path}'...")
    os.makedirs(save_path, exist_ok=True)
    model.save(save_path)
    print("Model downloaded and saved successfully!")

if __name__ == "__main__":
    download()
