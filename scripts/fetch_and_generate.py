#!/usr/bin/env python3
"""Auto-generate Android UI/UX Meta Repo — README + data.json + web app."""
import os, json, re, subprocess
from datetime import datetime, timedelta
from collections import defaultdict
import requests

TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {"Accept": "application/vnd.github+json"}

TOPICS = ["android-ui", "jetpack-compose", "android-animation", "android-library", "android-compose"]
MIN_STARS = 300
PER_TOPIC = 50

def repo_info():
    try:
        url = subprocess.check_output(["git","config","--get","remote.origin.url"], text=True).strip()
        parts = url.replace(":", "/").rstrip(".git").split("/")
        return parts[-2], parts[-1]
    except Exception:
        return "vukiengiang2025-sys", "android-ui-meta"

OWNER, NAME = repo_info()
PAGES_URL = f"https://{OWNER}.github.io/{NAME}/"

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def fetch(topic):
    url = "https://api.github.com/search/repositories"
    params = {"q": f"topic:{topic} stars:>={MIN_STARS}", "sort": "stars", "order": "desc", "per_page": PER_TOPIC}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 200:
            return r.json().get("items", [])
        print(f"  ⚠️  {topic}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  ⚠️  {topic}: {e}")
    return []

def classify(repo):
    hay = " ".join([repo.get("name",""), repo.get("description") or "", " ".join(repo.get("topics", []))]).lower()
    if "multiplatform" in hay or " kmp" in hay or "kmp " in hay:
        return "Compose Multiplatform"
    if "compose" in hay:
        return "Jetpack Compose"
    if any(k in hay for k in ["animation","lottie","motion","transition","shimmer","effect"]):
        return "Animation & Motion"
    if any(k in hay for k in ["image","glide","coil","picasso","fresco","photo","camera","media","video"]):
        return "Image & Media"
    if any(k in hay for k in ["material","design","theme","color","font","icon","typography"]):
        return "Material & Design"
    if any(k in hay for k in ["chart","graph","calendar","picker","dialog","sheet","pager","banner","carousel","menu","button","layout"]):
        return "UI Components"
    return "Other"

def activity(repo):
    if repo.get("archived"): return "archived"
    pushed = repo.get("pushed_at")
    if not pushed: return "unknown"
    dt = datetime.strptime(pushed, "%Y-%m-%dT%H:%M:%SZ")
    age = datetime.utcnow() - dt
    if age < timedelta(days=180): return "active"
    if age < timedelta(days=365): return "maintained"
    return "stale"

def collect():
    print(f"🔍 Fetching {len(TOPICS)} topics (min ⭐ {MIN_STARS})...")
    seen = {}
    for t in TOPICS:
        items = fetch(t)
        print(f"  → {t}: {len(items)} repos")
        for r in items:
            fn = r["full_name"]
            if fn in seen: continue
            seen[fn] = {
                "name": r["name"], "full_name": fn, "url": r["html_url"],
                "description": r.get("description") or "",
                "stars": r["stargazers_count"], "forks": r["forks_count"],
                "language": r.get("language") or "",
                "topics": r.get("topics", []),
                "license": (r.get("license") or {}).get("spdx_id") or "",
                "archived": bool(r.get("archived")),
                "pushed_at": r.get("pushed_at") or "",
                "category": classify(r), "status": activity(r),
            }
    print(f"✅ Tổng cộng: {len(seen)} repos unique")
    return list(seen.values())

STATUS_EMOJI = {"active":"🟢","maintained":"🟡","stale":"🔴","archived":"⚫","unknown":"⚪"}

def gen_readme(repos):
    by_cat = defaultdict(list)
    for r in repos: by_cat[r["category"]].append(r)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    L = []
    L.append("# 📱 Android UI/UX Meta Repo\n")
    L.append("> 🤖 **Tự động cập nhật mỗi ngày** — Tổng hợp các thư viện UI/UX Android chất lượng cao.\n")
    L.append(f"### 🌐 [**Mở trang duyệt trực quan** → search · filter · sort]({PAGES_URL})\n")
    L.append(f"📊 **{len(repos)}** thư viện · 🕐 Cập nhật: `{ts}`\n")
    L.append("---\n")
    L.append("## 📑 Mục lục\n")
    for cat in sorted(by_cat.keys()):
        L.append(f"- **[{cat}](#{slug(cat)})** — {len(by_cat[cat])} thư viện")
    L.append("")
    L.append("**Chú thích:** 🟢 Active (<6 tháng) · 🟡 Maintained (<1 năm) · 🔴 Stale (>1 năm) · ⚫ Archived\n")
    L.append("---\n")
    for cat in sorted(by_cat.keys()):
        L.append(f"## {cat}\n")
        L.append("| Repository | ⭐ Stars | Trạng thái | Mô tả |")
        L.append("|---|---:|---:|---|")
        for r in sorted(by_cat[cat], key=lambda x: -x["stars"]):
            d = r["description"][:120].replace("|","\\|").replace("\n"," ")
            if len(r["description"]) > 120: d += "..."
            L.append(f"| [{r['full_name']}]({r['url']}) | {r['stars']:,} | {STATUS_EMOJI[r['status']]} | {d or '—'} |")
        L.append("")
    L.append("---")
    L.append(f"\n> Được tạo tự động bởi [GitHub Actions](.github/workflows/update-meta.yml) · [JSON thô]({PAGES_URL}data.json)\n")
    with open("README.md","w",encoding="utf-8") as f: f.write("\n".join(L))
    print("  📝 README.md")

def gen_json(repos):
    with open("docs/data.json","w",encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, separators=(",",":"))
    print(f"  📦 docs/data.json ({len(repos)} entries)")

HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Android UI/UX Library Explorer</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
  .line-clamp-2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
<header class="border-b border-slate-800 bg-slate-900/70 sticky top-0 backdrop-blur z-10">
  <div class="max-w-7xl mx-auto px-4 py-4">
    <div class="flex items-center justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">📱 Android UI/UX Explorer</h1>
        <p class="text-slate-400 text-sm mt-1">Tự động cập nhật · <span id="count" class="font-semibold text-emerald-400">0</span> thư viện</p>
      </div>
      <a href="https://github.com/REPO_OWNER_PLACEHOLDER/REPO_NAME_PLACEHOLDER" target="_blank" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm">⭐ GitHub</a>
    </div>
    <div class="mt-4 grid grid-cols-1 md:grid-cols-4 gap-2">
      <input id="search" type="text" placeholder="🔍 Tìm tên, mô tả, topic..." class="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 focus:border-emerald-500 outline-none text-sm">
      <select id="category" class="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm"><option value="">Mọi category</option></select>
      <select id="status" class="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm">
        <option value="">Mọi trạng thái</option>
        <option value="active">🟢 Active</option>
        <option value="maintained">🟡 Maintained</option>
        <option value="stale">🔴 Stale</option>
        <option value="archived">⚫ Archived</option>
      </select>
      <select id="sort" class="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm">
        <option value="stars">⭐ Sao giảm dần</option>
        <option value="updated">🕐 Mới cập nhật</option>
        <option value="name">🔤 Tên A→Z</option>
      </select>
    </div>
  </div>
</header>
<main class="max-w-7xl mx-auto px-4 py-6">
  <div id="grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
  <p id="empty" class="hidden text-center text-slate-500 py-12">Không tìm thấy kết quả 😕</p>
</main>
<footer class="text-center text-xs text-slate-600 py-6 border-t border-slate-800 mt-12">
  Tự động bởi GitHub Actions · <a href="data.json" class="hover:text-emerald-400">data.json</a>
</footer>
<script>
let allData=[];
const SE={active:'🟢',maintained:'🟡',stale:'🔴',archived:'⚫',unknown:'⚪'};
const esc=s=>(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
fetch('data.json').then(r=>r.json()).then(data=>{
  allData=data;
  document.getElementById('count').textContent=data.length;
  const cats=[...new Set(data.map(d=>d.category))].sort();
  const catSel=document.getElementById('category');
  cats.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;catSel.appendChild(o)});
  render();
}).catch(e=>console.error(e));
function render(){
  const q=document.getElementById('search').value.toLowerCase();
  const cat=document.getElementById('category').value;
  const st=document.getElementById('status').value;
  const sort=document.getElementById('sort').value;
  let f=allData.filter(d=>{
    if(q&&!(d.name.toLowerCase().includes(q)||(d.description||'').toLowerCase().includes(q)||d.topics.join(' ').toLowerCase().includes(q)))return false;
    if(cat&&d.category!==cat)return false;
    if(st&&d.status!==st)return false;
    return true;
  });
  f.sort((a,b)=>sort==='stars'?b.stars-a.stars:sort==='name'?a.name.localeCompare(b.name):(b.pushed_at||'').localeCompare(a.pushed_at||''));
  document.getElementById('empty').classList.toggle('hidden',f.length>0);
  document.getElementById('grid').innerHTML=f.map(d=>`
    <a href="${d.url}" target="_blank" rel="noopener" class="block p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500 hover:bg-slate-900/80 transition group">
      <div class="flex items-start justify-between gap-2">
        <h3 class="font-semibold truncate group-hover:text-emerald-400">${esc(d.name)}</h3>
        <span class="text-xs flex-shrink-0">${SE[d.status]||'⚪'}</span>
      </div>
      <p class="text-xs text-slate-500 truncate mt-0.5">${esc(d.full_name)}</p>
      <p class="text-sm text-slate-400 mt-2 line-clamp-2 h-10">${esc(d.description||'Không có mô tả')}</p>
      <div class="flex flex-wrap gap-1 mt-3">
        <span class="px-2 py-0.5 rounded text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">${esc(d.category)}</span>
        ${d.language?`<span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400">${esc(d.language)}</span>`:''}
      </div>
      <div class="flex items-center gap-3 mt-3 text-xs text-slate-400">
        <span>⭐ ${d.stars.toLocaleString()}</span>
        <span>🍴 ${d.forks.toLocaleString()}</span>
      </div>
    </a>`).join('');
}
['search','category','status','sort'].forEach(id=>document.getElementById(id).addEventListener('input',render));
</script>
</body>
</html>
"""

def gen_html():
    html = HTML.replace("REPO_OWNER_PLACEHOLDER", OWNER).replace("REPO_NAME_PLACEHOLDER", NAME)
    with open("docs/index.html","w",encoding="utf-8") as f: f.write(html)
    print("  🌐 docs/index.html")

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    repos = collect()
    gen_readme(repos)
    gen_json(repos)
    gen_html()
    print(f"\n🎉 Done! {len(repos)} repos → README + web app")
