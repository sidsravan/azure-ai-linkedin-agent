This is an AI-powered automation tool that:

Finds the latest Microsoft Azure & AI news from official blogs

Creates a LinkedIn post from that news (beginner-friendly)

Optionally finds Azure/DevOps jobs to include in posts

Can automatically post to LinkedIn from your computer

Think of it as your personal social media assistant that reads tech news and writes LinkedIn posts for you!
Every Friday at 9:30 AM IST:

┌─────────────────────────────────────┐
│  GitHub Actions (Cloud)             │
│  ├─ Fetches latest Azure news       │
│  ├─ Generates LinkedIn post         │
│  └─ Saves as downloadable file      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  You (Any time on Friday)           │
│  ├─ Download the post from GitHub   │
│  ├─ Run: python publish.py          │
│  └─ Post appears on LinkedIn!       │
└─────────────────────────────────────┘

# If using Git:
git clone https://github.com/YOUR_USERNAME/azure-ai-linkedin-agent.git
cd azure-ai-linkedin-agent

# On Mac/Linux:
chmod +x setup.sh
./setup.sh

# On Windows:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Create .env file:
cp .env.example .env

# Edit .env file and add your details:
nano .env  # or open in any text editor
Add your linked in credentials in .env file
LINKEDIN_EMAIL=yourname@gmail.com
LINKEDIN_PASSWORD=yourlinkedinpassword
MODEL_NAME=template

# run from your local
 # for login 
    (venv) PS D:\Sravan\AI\agent\azure-ai-linkedin-agent>  python publish.py --login-only
# for post and confirm with yes
    (venv) PS D:\Sravan\AI\agent\azure-ai-linkedin-agent> python publish.py --post-id 3

# OR just download ZIP and extract
azure-ai-linkedin-agent/
│
├── 📂 .github/workflows/          # GitHub Automation
│   └── friday_post.yml             # → Runs every Friday automatically
│                                   #   Generates post without you doing anything
│
├── 📂 src/                         # Main Code (The Brain)
│   ├── news_fetcher.py             # → Goes to Microsoft blogs, gets latest news
│   ├── content_generator.py        # → Converts news into LinkedIn posts using AI
│   ├── post_formatter.py           # → Makes posts look good, saves history
│   ├── linkedin_publisher.py       # → Opens LinkedIn, types post, clicks Post
│   ├── job_scraper.py              # → Finds latest Azure/DevOps jobs on LinkedIn
│   └── utils.py                    # → Common helper functions
│
├── 📂 data/                        # Storage (Auto-created)
│   ├── ready_to_post.txt           # → Your generated post (copy from here)
│   ├── post_history.json           # → All posts ever created
│   ├── latest_news.json            # → Latest fetched news
│   └── jobs.json                   # → Latest job listings
│
├── main.py                         # → 🔑 GENERATE POST (Run this to create post)
├── publish.py                      # → 🔑 PUBLISH TO LINKEDIN (Run this to post)
├── publish_manual.py               # → Alternative: Copy & Paste method
│
├── requirements.txt                # → List of Python packages needed
├── .env                            # → Your passwords (CREATE THIS FILE)
├── .env.example                    # → Template for .env file
├── Makefile                        # → Shortcut commands
├── setup.sh                        # → One-click installation
│
└── README.md                       # → This file 📖

# Generate only (no publishing)
python main.py --model template

# List all posts
python publish.py --list

# Publish specific post
python publish.py --post-id 3

# Dry run (test without posting)
python publish.py --dry-run

# Re-authenticate LinkedIn
python publish.py --login-only


# lin from local for login check

(venv) PS D:\Sravan\AI\agent\azure-ai-linkedin-agent> python publish.py --login-only

