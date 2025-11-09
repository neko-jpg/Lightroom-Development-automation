# Statistics Widget - Quick Start Guide

## Overview

The Statistics Widget provides comprehensive reporting and analysis for the Junmai AutoDev system.

## Quick Start

### 1. Installation

Ensure all dependencies are installed:

```bash
# Required
pip install PyQt6 requests

# Optional (for full functionality)
pip install matplotlib reportlab
```

### 2. Start the API Server

```bash
cd local_bridge
python app.py
```

The API server should be running at `http://localhost:5100`

### 3. Run the Test

```bash
cd gui_qt
python test_statistics_visual.py
```

## Features

### 📊 Overview Tab

**Summary Metrics:**
- Total Photos
- Processed Photos
- Approved Photos
- Success Rate
- Average Processing Time
- Time Saved

**Statistics Sections:**
- Processing Pipeline Statistics
- Quality Metrics

### 📈 Charts Tab

**Visualizations:**
- Processing Activity Bar Chart (7-day history)
- Refresh button for manual updates

**Requirements:** matplotlib

### 🎨 Presets Tab

**Preset Analysis:**
- Usage frequency list
- Visual percentage bars
- Pie chart visualization
- Sorted by usage count

## Usage

### Period Selection

Switch between time periods:
- **Daily**: Today's statistics
- **Weekly**: Past 7 days
- **Monthly**: Current month

### Export Data

**CSV Export:**
1. Click "📄 Export CSV"
2. Choose save location
3. File includes all metrics and preset usage

**PDF Export:**
1. Click "📑 Export PDF"
2. Choose save location
3. Professional report with tables and formatting

**Requirements:** reportlab (for PDF)

### View Charts

**Processing Activity:**
1. Go to Charts tab
2. Click "🔄 Refresh Charts"
3. View bar chart of daily activity

**Preset Usage:**
1. Go to Presets tab
2. Click "📊 Show Chart"
3. View pie chart of preset distribution

## API Endpoints Used

```
GET /statistics/daily       - Daily statistics
GET /statistics/weekly      - Weekly statistics
GET /statistics/monthly     - Monthly statistics
GET /statistics/presets     - Preset usage data
```

## Troubleshooting

### "Failed to load statistics"

**Cause:** API server not running or unreachable

**Solution:**
```bash
cd local_bridge
python app.py
```

### "Matplotlib not installed"

**Cause:** Optional dependency missing

**Solution:**
```bash
pip install matplotlib
```

### "ReportLab library is not installed"

**Cause:** Optional dependency missing for PDF export

**Solution:**
```bash
pip install reportlab
```

### No data displayed

**Cause:** No photos processed yet

**Solution:** Process some photos first or use test data

## Integration

### Add to Main Window

```python
from widgets.statistics_widgets import StatisticsWidget

# Create widget
statistics = StatisticsWidget(api_base_url="http://localhost:5100")

# Add to tab widget
tab_widget.addTab(statistics, "📊 Statistics")
```

### Standalone Usage

```python
from PyQt6.QtWidgets import QApplication
from widgets.statistics_widgets import StatisticsWidget

app = QApplication([])
widget = StatisticsWidget()
widget.show()
app.exec()
```

## Configuration

### API Base URL

Default: `http://localhost:5100`

Custom:
```python
widget = StatisticsWidget(api_base_url="http://custom-host:5100")
```

### Update Intervals

- Statistics: 30 seconds
- Preset usage: 60 seconds

## Keyboard Shortcuts

- **Tab**: Navigate between tabs
- **Ctrl+E**: Export (when focused on export button)
- **F5**: Refresh (when focused on refresh button)

## Tips

1. **Performance**: Charts are generated on-demand to save resources
2. **Export**: Use CSV for data analysis, PDF for reports
3. **Period**: Switch periods to see trends over time
4. **Presets**: Monitor which presets are most effective
5. **Time Saved**: Track efficiency improvements

## Examples

### Daily Workflow

1. Open Statistics tab
2. Check today's summary metrics
3. Review success rate
4. Export CSV for records

### Weekly Review

1. Switch to Weekly period
2. Generate processing activity chart
3. Review preset usage
4. Export PDF report

### Monthly Analysis

1. Switch to Monthly period
2. Compare with previous months
3. Identify trends
4. Adjust presets based on data

## Support

For issues or questions:
1. Check STATISTICS_IMPLEMENTATION.md for details
2. Review TASK_28_COMPLETION_SUMMARY.md
3. Check API server logs
4. Verify database has data

## Files

- `widgets/statistics_widgets.py` - Main implementation
- `test_statistics.py` - Basic test
- `test_statistics_visual.py` - Visual test
- `STATISTICS_IMPLEMENTATION.md` - Full documentation
- `STATISTICS_QUICK_START.md` - This file

---

**Version:** 1.0  
**Last Updated:** 2025-11-09  
**Status:** Production Ready
