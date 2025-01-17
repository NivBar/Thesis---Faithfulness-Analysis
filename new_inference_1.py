from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import warnings
import pandas as pd
from tqdm import tqdm

warnings.filterwarnings("ignore")
cuda_available = torch.cuda.is_available()
print("CUDA Available:", cuda_available)

file_name = "/lv_local/home/niv.b/llama/bot_followup_files/part_1.csv"
orig = pd.read_csv(file_name)
p_df = orig[orig.text.isna()].copy()
token = 'hugging_face_token'
# tokenizer = AutoTokenizer.from_pretrained(name, use_auth_token=token, use_fast=True)

model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id,use_auth_token=token)

terminators = [
    tokenizer.eos_token_id,
    tokenizer.convert_tokens_to_ids("<|eot_id|>")
]

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    use_auth_token=token,
)


for idx, row in tqdm(p_df.iterrows(), total=p_df.shape[0], desc="Generating responses"):
    try:
        messages = eval(row['prompt'])

        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)

        outputs = model.generate(
            input_ids,
            max_new_tokens=256,
            eos_token_id=terminators,
            do_sample=True,
            temperature=0.5,
            top_p=0.9,
        )
        response = outputs[0][input_ids.shape[-1]:]
        try:
            text_output = tokenizer.decode(response, skip_special_tokens=True).replace("\\n", "\n")
            if 'document:' in text_output:
                text_output = text_output.split('document:')[1].strip().split('\n\n')[0].strip()
            elif 'documents:' in text_output:
                text_output = text_output.split('\n\n')[2].strip()
            elif len(text_output.split('\n\n')) > 1:
                text_output = text_output.split('\n\n')[1].strip()
            else:
                try:
                    text_output = text_output.split('\n\n', 1)[1]
                except:
                    pass
                if 'Note:' in text_output:
                    text_output = text_output.split('Note:')[0].strip()

            orig.loc[row.name, "text"] = text_output
            orig.to_csv(file_name, index=False)

        except Exception as e:
            print('idx: ', idx, ' - error: ', e)
            continue

    except Exception as e:
        print('idx: ', idx, ' - error: ', e)
        continue



