import json
import subprocess


def merge_rules(rules_file, add_rules_file):
    # Đọc nội dung từ rules.json
    with open(rules_file, 'r', encoding='utf-8') as rf:
        try:
            rules = json.load(rf)
        except json.JSONDecodeError:
            rules = []

    # Đọc nội dung từ add_rules.json
    with open(add_rules_file, 'r', encoding='utf-8') as arf:
        try:
            add_rules = json.load(arf)
        except json.JSONDecodeError:
            add_rules = []

    # Tìm ID lớn nhất hiện tại trong rules.json
    max_id = max((rule.get('id', 0) for rule in rules), default=0)

    # Gán ID mới cho các rule trong add_rules.json
    for idx, rule in enumerate(add_rules, start=1):
        rule['id'] = max_id + idx

    # Kết hợp rules.json và add_rules.json
    merged_rules = rules + add_rules

    # Loại bỏ các rule trùng lặp (so sánh toàn bộ rule trừ ID)
    seen = set()
    unique_rules = []
    for rule in merged_rules:
        rule_key = json.dumps({k: v for k, v in rule.items() if k != 'id'}, sort_keys=True)
        if rule_key not in seen:
            seen.add(rule_key)
            unique_rules.append(rule)

    # Cập nhật lại ID để liên tục
    for idx, rule in enumerate(unique_rules, start=1):
        rule['id'] = idx

    # Ghi lại rules.json với nội dung đã hợp nhất và loại bỏ trùng lặp
    with open(rules_file, 'w', encoding='utf-8') as wf:
        json.dump(unique_rules, wf, indent=2, ensure_ascii=False)

    # Giữ nguyên định dạng của add_rules.json
    with open(add_rules_file, 'r', encoding='utf-8') as af:
        original_format = af.read()

    # Ghi lại add_rules.json với nội dung rỗng nhưng giữ định dạng cũ
    empty_json = "[]"  # Nội dung rỗng
    if original_format.startswith("[\n") and original_format.endswith("\n]"):
        empty_json = "[\n\n]"  # Giữ nguyên xuống dòng

    with open(add_rules_file, 'w', encoding='utf-8') as af:
        af.write(empty_json)

    print(f"Đã hợp nhất {len(add_rules)} rule(s) vào {rules_file}, loại bỏ trùng lặp và cập nhật ID.")


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
    # Đường dẫn file
    rules_file_path = "custom_rules.json"
    add_rules_file_path = "add_rules.json"

    # Git user và email
    git_user = "github-actions[bot]"  # Thay bằng tên người dùng của bạn nếu cần
    git_email = "github-actions[bot]@users.noreply.github.com"

    # Lời nhắn commit
    commit_msg = "Auto update rules.json and clear add_rules.json: Merged and removed duplicates"

    # Cấu hình Git
    configure_git(git_user, git_email)

    # Gọi hàm hợp nhất và loại bỏ trùng lặp
    merge_rules(rules_file_path, add_rules_file_path)

    # Commit và push cả hai file
    git_commit_and_push([rules_file_path, add_rules_file_path], commit_msg)
