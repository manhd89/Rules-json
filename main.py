import json
import subprocess


def merge_rules(output_file, input_files):
    combined_rules = []
    seen = set()

    # Đọc và hợp nhất các file input
    for file in input_files:
        with open(file, 'r', encoding='utf-8') as f:
            try:
                rules = json.load(f)
            except json.JSONDecodeError:
                rules = []
            for rule in rules:
                rule_key = json.dumps({k: v for k, v in rule.items() if k != 'id'}, sort_keys=True)
                if rule_key not in seen:
                    seen.add(rule_key)
                    combined_rules.append(rule)

    # Sắp xếp lại ID để liên tục
    for idx, rule in enumerate(combined_rules, start=1):
        rule['id'] = idx

    # Kiểm tra tổng số lượng rules
    total_rules = len(combined_rules)
    print(f"Tổng số rules sau khi hợp nhất: {total_rules}")
    if total_rules > 150000:
        print("⚠️ Cảnh báo: Tổng số rules đã vượt quá giới hạn 150,000!")
    else:
        print("✅ Số lượng rules nằm trong giới hạn cho phép (<= 150,000).")

    # Ghi ra file output
    with open(output_file, 'w', encoding='utf-8') as of:
        json.dump(combined_rules, of, separators=(',', ':'), ensure_ascii=False)

    print(f"Đã hợp nhất {len(input_files)} file thành {output_file}, loại bỏ trùng lặp.")


def configure_git(username, email):
    try:
        # Thiết lập Git user và email
        subprocess.run(["git", "config", "--global", "user.name", username], check=True)
        subprocess.run(["git", "config", "--global", "user.email", email], check=True)
        print(f"Cấu hình Git với user: {username}, email: {email}")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi cấu hình Git: {e}")


def git_commit_and_push(files, commit_message):
    try:
        # Add file vào staging
        subprocess.run(["git", "add"] + files, check=True)

        # Commit với thông điệp
        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # Push lên remote repository
        subprocess.run(["git", "push"], check=True)

        print("Đã commit và đẩy thay đổi lên GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi thực hiện Git: {e}")


if __name__ == "__main__":
    # Danh sách file input
    input_files = [
        "dnr_ads.json",
        "dnr_annoyances.json",
        "dnr_tracking.json",
        "dnr_lang-vi.json",
        "dnr_fixes.json",
        "add_rules.json",
    ]
    
    # File output
    output_file = "rules.json"

    # Git user và email
    git_user = "github-actions[bot]"  # Thay bằng tên người dùng nếu cần
    git_email = "github-actions[bot]@users.noreply.github.com"

    # Lời nhắn commit
    commit_msg = "Auto update rules.json: Combined files and removed duplicates"

    # Cấu hình Git
    configure_git(git_user, git_email)

    # Hợp nhất rules và loại bỏ trùng lặp
    merge_rules(output_file, input_files)

    # Commit và push file output
    git_commit_and_push([output_file], commit_msg)
