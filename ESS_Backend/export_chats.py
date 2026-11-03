import json
import os
from pathlib import Path

# Path where Antigravity stores conversation logs
brain_dir = Path(r"C:\Users\ravi.mallem\.gemini\antigravity\brain")

# Target folder in your project where you want chats saved
output_dir = Path(r"D:\Antigravity_Chats\chat_history_oct")
output_dir.mkdir(parents=True, exist_ok=True)

for conv_dir in brain_dir.iterdir():
    if not conv_dir.is_dir():
        continue
    
    transcript_file = conv_dir / ".system_generated" / "logs" / "transcript_full.jsonl"
    if not transcript_file.exists():
        transcript_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
    
    if not transcript_file.exists():
        continue

    md_output = [f"# Conversation {conv_dir.name}\n"]
    
    with open(transcript_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
                role = item.get("source", "")
                step_type = item.get("type", "")
                content = item.get("content", "")
                
                if step_type == "USER_INPUT":
                    md_output.append(f"### 👤 User\n\n{content}\n")
                elif step_type == "PLANNER_RESPONSE" and content:
                    md_output.append(f"### 🤖 Assistant\n\n{content}\n")
            except Exception:
                continue

    out_file = output_dir / f"{conv_dir.name}.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n---\n".join(md_output))

print(f"Exported conversations to {output_dir}")