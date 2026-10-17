def repo_mem():
  import os, datetime
  timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
  repos = [i for i in os.listdir("/data/Brain") if os.path.isdir(f"/data/Brain/{i}") and not i.startswith(".")]
  with open(f"/data/mcp_server/state/repo_mem_{timestamp}.md", "w") as f:
    f.write(f"# Repository Memory {timestamp}\n" + "\n".join([f"- {r}" for r in repos]))
  return f"Success! {len(repos)} repos indexed"
if __name__ == "__main__": print(repo_mem())
