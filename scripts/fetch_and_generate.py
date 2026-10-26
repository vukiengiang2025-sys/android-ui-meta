#!/usr/bin/env python3
"""
Script tự động lấy dữ liệu các repo UI/UX Android từ GitHub API
và tạo file README.md được phân loại.
(Đây là phiên bản đơn giản, có thể nâng cấp sau)
"""
import os
import requests
import json

# Cấu hình
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
# Các chủ đề (topic) muốn theo dõi
TOPICS = ["android-ui", "jetpack-compose", "android-animation", "android-library"]
MIN_STARS = 500

def fetch_repos(topic):
    """Lấy danh sách repo theo topic, sắp xếp theo star giảm dần."""
    url = f"https://api.github.com/search/repositories?q=topic:{topic}+stars:>={MIN_STARS}&sort=stars&order=desc&per_page=10"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("items", [])
    print(f"Lỗi khi lấy dữ liệu cho topic {topic}: {response.status_code}")
    return []

def generate_readme():
    """Tạo nội dung README từ dữ liệu đã lấy."""
    content = "# 📱 Android UI/UX Meta Repo\n\n"
    content += "> Danh sách được tổng hợp tự động hàng ngày từ GitHub.\n\n"
    
    all_repos = {}
    for topic in TOPICS:
        print(f"Đang lấy dữ liệu cho topic: {topic}...")
        repos = fetch_repos(topic)
        if repos:
            all_repos[topic] = repos

    for topic, repos in all_repos.items():
        content += f"## {topic.replace('-', ' ').title()}\n\n"
        content += "| Repository | Stars | Description |\n"
        content += "|---|---|---|\n"
        for repo in repos:
            name = repo.get("full_name", "N/A")
            stars = repo.get("stargazers_count", 0)
            desc = repo.get("description", "Không có mô tả") or "Không có mô tả"
            # Cắt ngắn mô tả nếu quá dài
            if len(desc) > 100: desc = desc[:97] + "..."
            content += f"| [{name}](https://github.com/{name}) | ⭐ {stars} | {desc} |\n"
        content += "\n"
    
    # Ghi đè file README.md
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Đã tạo xong README.md")

if __name__ == "__main__":
    generate_readme()
