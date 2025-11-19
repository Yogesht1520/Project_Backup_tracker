****Backup Tracker and System Monitoring****
A React-based dashboard for monitoring backup jobs, detecting anomalies, visualizing metrics, and providing insights into backup system performance. It utilizes React 19, Vite, TailwindCSS, and Chart.js, designed to connect to a backup-tracking backend API for a real-time interface.

---

## 🚀 Features

### 📊 **Dashboard Overview**
- High-level system status
- Backup success/failure summaries
- Key metrics and quick-glance statistics

### 🕒 **Timeline View**
- Visual representation of backup job timelines  
- Filter by job type, status, or time range

### 💾 **Vault Management**
- Display storage vaults and their current capacity  
- Monitor vault health and usage trends

### ⚙️ **Jobs Monitoring**
- Track all backup jobs  
- Status indicators (success, failed, running, queued)  
- Job details and history

### 🔍 **Anomaly Detection**
- View anomalies detected from backup operations  
- Quick navigation to root cause insights

### 📡 **Live Metrics**
- Real-time metrics dashboard using Chart.js  
- Auto-refreshing visualization panels

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-------------|
| Framework | **React 19** |
| Build Tool | **Vite** |
| Styling | **TailwindCSS** |
| Charts | **Chart.js** |
| Routing | **React Router** |
| Linting | **ESLint** |
| Dev Features | Hot Module Reloading, React Compiler |

---

## 📂 Project Structure

src/
├── components/        # Reusable UI components
├── pages/             # Main app pages (Dashboard, Jobs, Timeline, etc.)
├── assets/            # Images, icons, etc.
├── App.jsx            # Main app container
├── main.jsx           # Entry point
└── config.js          # API endpoints or environment config
```



## ▶️ Getting Started

### **1. Install dependencies**
```bash
npm install
```
2. Run development server
   npm run dev

3. Build for production
   npm run build

4. Preview production build
   npm run preview

⚙️ Configuration

- Update src/config.js to point to your backend API:
export const API_BASE_URL = "http://your-backend.url/api";
