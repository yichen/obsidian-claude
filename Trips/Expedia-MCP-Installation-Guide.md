# Expedia MCP Server Installation Guide

Complete guide to installing and configuring the Expedia Travel Recommendations MCP server for Claude Code (VSCode), Claude Desktop, and ChatGPT Desktop.

---

## Overview

The Expedia MCP server provides access to:
- 🏨 **Hotels** with pricing and filtering
- ✈️ **Flights** with comparison
- 🚗 **Car rentals**
- 🗺️ **Activities**

**Source:** [Expedia Group Official MCP Server](https://github.com/ExpediaGroup/expedia-travel-recommendations-mcp)

---

## Step 1: Get an Expedia API Key

### ⚠️ Important Note
The Expedia API requires **partner approval** and is primarily for travel businesses, not individual consumers. This may be a blocker for personal use.

### Application Process

1. **Register at Expedia Developer Hub**
   - Visit: https://developers.expediagroup.com
   - Create an account on Expedia Partner Solutions

2. **Submit API Application Form**
   - Navigate to API products (e.g., Rapid API for hotels)
   - Complete the partner application
   - **Approval time:** 2-3 months (according to documentation)

3. **Get Your Credentials**
   - Once approved, log into the Expedia Partner Console
   - Go to **Connectivity** → **API key**
   - Create an API client and **save your credentials securely**
   - Note: Credentials are only shown once during creation

### Alternative Approach
If you can't get official Expedia API access, consider:
- Using the **MCP Travel Assistant** (uses SerpAPI instead) - see Alternative Servers section below
- Sticking with manual comparison for now

---

## Step 2: Install Prerequisites

### For All Methods

**Python 3.11 or higher:**
```bash
# Check your Python version
python3 --version

# If you need to install Python 3.11+
# macOS (using Homebrew)
brew install python@3.11

# Windows: Download from python.org
```

**Install uvx (recommended for CLI installation):**
```bash
# macOS/Linux
pip3 install uv

# Windows
pip install uv
```

---

## Step 3: Installation by Application

---

## 🖥️ Claude Code (VSCode Extension)

### Method 1: GUI Installation (Easiest)

1. **Open VSCode with Claude Code extension installed**

2. **Open Command Palette** (Cmd/Ctrl + Shift + P)

3. **Type:** `MCP: Browse Servers`

4. **Manually add Expedia MCP:**
   - If Expedia isn't in the list, you'll need to use Method 2

### Method 2: Manual Configuration (Recommended)

**For workspace-specific setup:**

1. **Create MCP configuration file** in your project:
   ```bash
   # In your project root
   mkdir -p .vscode
   touch .vscode/mcp.json
   ```

2. **Edit `.vscode/mcp.json`:**
   ```json
   {
     "mcpServers": {
       "expedia-travel": {
         "command": "uvx",
         "args": [
           "expedia_travel_recommendations_mcp",
           "--protocol",
           "stdio"
         ],
         "env": {
           "EXPEDIA_API_KEY": "YOUR_API_KEY_HERE"
         }
       }
     }
   }
   ```

3. **Reload VSCode window** (Cmd/Ctrl + Shift + P → "Reload Window")

4. **Verify in MCP Servers panel:**
   - Open the MCP Servers view in VSCode sidebar
   - You should see "expedia-travel" listed
   - Right-click → Start Server

**For global setup (all projects):**

1. **Open VSCode Settings** (Cmd/Ctrl + ,)

2. **Search for:** `mcp`

3. **Edit settings.json** (click the "{}" icon in top right)

4. **Add the same configuration** as above to your user settings

---

## 🖥️ Claude Desktop

### Configuration Steps

1. **Open Claude Desktop Settings**
   - macOS: Click **Claude menu** in menu bar → **Settings**
   - Windows: Click **Settings** in app menu

2. **Go to Developer Tab**

3. **Click "Edit Config"** button
   - This opens the config file in your default editor
   - Creates the file if it doesn't exist

4. **Add Expedia MCP configuration:**

   ```json
   {
     "mcpServers": {
       "expedia-travel-recommendations": {
         "command": "uvx",
         "args": [
           "expedia_travel_recommendations_mcp",
           "--protocol",
           "stdio"
         ],
         "env": {
           "EXPEDIA_API_KEY": "YOUR_API_KEY_HERE"
         }
       }
     }
   }
   ```

5. **Save the file**

6. **Restart Claude Desktop** (completely quit and reopen)

7. **Verify installation:**
   - Start a new conversation
   - Type: "What MCP servers are available?"
   - Claude should list "expedia-travel-recommendations"

### Configuration File Locations

**Manual editing (if needed):**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```bash
# macOS: Open config file directly
open ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Windows (PowerShell)
notepad $env:APPDATA\Claude\claude_desktop_config.json
```

---

## 💬 ChatGPT Desktop

### Important Limitations

⚠️ **ChatGPT Desktop cannot connect to localhost servers** - you'll need a tunnel service like ngrok.

### Option 1: Using Docker + ngrok (Recommended for ChatGPT)

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop/

2. **Start Expedia MCP with Docker:**
   ```bash
   docker run -d \
     -p 9900:9900 \
     -e EXPEDIA_API_KEY=YOUR_API_KEY_HERE \
     --name expedia-mcp \
     expediagroup/expedia-travel-recommendations-mcp
   ```

3. **Install ngrok:**
   ```bash
   # macOS
   brew install ngrok

   # Windows: Download from https://ngrok.com/download
   ```

4. **Create ngrok tunnel:**
   ```bash
   ngrok http 9900
   ```

5. **Copy the HTTPS forwarding URL** (looks like `https://xxxx-xx-xxx-xxx-xxx.ngrok-free.app`)

6. **Configure ChatGPT Desktop:**
   - Open **ChatGPT Desktop** app
   - Go to **Settings** → **Connectors** → **Advanced** → **Developer Mode**
   - Click **Add Connector**
   - **Name:** Expedia Travel
   - **URL:** `https://your-ngrok-url.ngrok-free.app/mcp`
   - **Protocol:** SSE (Server-Sent Events)
   - Click **Save**

7. **Test the connection:**
   - Start a new chat
   - Ask: "Can you search for hotels in Hawaii for October 22-26?"

### Option 2: Cloud Deployment

If you have a cloud server (AWS, Digital Ocean, etc.):

1. **Deploy Expedia MCP on your server** using Docker
2. **Configure firewall** to allow HTTPS traffic on port 9900
3. **Add connector in ChatGPT** using your public server URL

---

## Step 4: Testing Your Installation

### For Claude Code / Claude Desktop

Try these test queries:

```
1. "Search for hotels in Kona, Hawaii from October 22-26, 2025"

2. "Find the cheapest flights from Seattle to Kona on October 22, 2025"

3. "Compare hotel prices in Kona, showing properties with ratings above 4 stars"

4. "What activities are available in Kona, Hawaii?"
```

### For ChatGPT Desktop

After configuring the connector:

```
1. "Use the Expedia Travel connector to search for hotels in Kona"

2. "Compare hotel prices for my Hawaii trip using Expedia"
```

---

## Troubleshooting

### "Command not found: uvx"

**Solution:** Install `uv` first:
```bash
pip3 install uv
```

### "API Key Invalid" or Authentication Errors

**Check:**
1. Your API key is correctly copied (no extra spaces)
2. Your Expedia developer account is approved
3. The API key hasn't expired

**Debug:**
```bash
# Test manually
export EXPEDIA_API_KEY="your_key_here"
uvx expedia_travel_recommendations_mcp --protocol stdio
```

### "MCP Server Not Starting" (Claude Desktop/Code)

**Solutions:**
1. Check Python version: `python3 --version` (must be 3.11+)
2. Try running manually to see error messages:
   ```bash
   export EXPEDIA_API_KEY="your_key_here"
   uvx expedia_travel_recommendations_mcp --protocol stdio
   ```
3. Check MCP server logs:
   - Claude Desktop: Settings → Developer → View Logs
   - Claude Code: MCP Servers panel → Right-click server → View Logs

### ChatGPT "Cannot Connect to Localhost"

**Solution:** Must use ngrok or cloud deployment (see ChatGPT section above)

### ngrok Connection Issues

**Solutions:**
1. Make sure Docker container is running: `docker ps`
2. Test localhost first: `curl http://localhost:9900/mcp`
3. Check ngrok is pointing to correct port (9900)
4. Try creating a new ngrok tunnel

---

## Alternative MCP Servers for Travel

If Expedia API access is blocked, consider these alternatives:

### 1. MCP Travel Assistant (No API Key Required)
- **GitHub:** https://github.com/skarlekar/mcp_travelassistant
- Uses SerpAPI (free tier available)
- Includes flights, hotels, weather, events

**Quick install:**
```bash
# Clone the repository
git clone https://github.com/skarlekar/mcp_travelassistant.git
cd mcp_travelassistant

# Follow setup instructions in README
```

### 2. Amadeus MCP (Alternative API)
- **GitHub:** https://github.com/soren-olympus/amadeus-mcp
- Amadeus API may be easier to get approved
- Similar hotel/flight search capabilities

### 3. Hotels MCP (Booking.com)
- **GitHub:** https://github.com/esakrissa/hotels_mcp_server
- Uses Booking.com API
- May have easier API access

---

## Usage Tips

### Effective Queries

**Good queries:**
```
✅ "Search for hotels in Kona, Hawaii from October 22-26, 2025,
   filter by rating above 4 stars, sort by cheapest"

✅ "Find flights from Seattle (SEA) to Kona (KOA) departing
   October 22, 2025, return October 26, 2025"

✅ "Compare 3-4 star hotels near Kailua-Kona with prices under $200/night"
```

**Poor queries:**
```
❌ "Find me a good hotel" (too vague)
❌ "What's the best deal?" (no context)
❌ "Book me a flight" (MCP shows prices, doesn't book)
```

### Combining with Manual Research

**Best workflow:**
1. Use **Expedia MCP** to get baseline prices quickly
2. Manually check **Costco Travel** and **Chase Travel Portal**
3. Calculate effective prices with your credit card rewards
4. Make final decision based on total value

### Security Best Practices

1. **Never commit API keys to git:**
   ```bash
   # Add to .gitignore
   echo ".vscode/mcp.json" >> .gitignore
   ```

2. **Use environment variables** for production:
   ```bash
   # Add to ~/.zshrc or ~/.bashrc
   export EXPEDIA_API_KEY="your_key_here"
   ```

3. **Rotate API keys periodically** (every 90 days recommended)

---

## Next Steps

After installation:

1. **Test with your Hawaii trip:**
   - "Search hotels in Kona from Oct 22-26"
   - Compare results with your Costco Travel list

2. **Create a comparison workflow:**
   - Document prices from Expedia MCP
   - Add Costco/Chase prices manually
   - Calculate rewards value

3. **Update your Trips/CLAUDE.md:**
   - Add notes about using MCP for price research
   - Document effective queries

---

## Support & Resources

**Official Documentation:**
- Expedia MCP: https://github.com/ExpediaGroup/expedia-travel-recommendations-mcp
- MCP Protocol: https://modelcontextprotocol.io/
- Claude Desktop MCP: https://support.claude.com/en/articles/10949351

**Getting Help:**
- Expedia Developer Support: https://developers.expediagroup.com
- MCP Discord: https://discord.gg/modelcontextprotocol
- Claude Support: https://support.claude.com

---

## Summary Checklist

### Before Installation
- [ ] Python 3.11+ installed
- [ ] Expedia API key obtained (or chose alternative MCP server)
- [ ] Decided which app(s) to configure (Claude Code, Desktop, ChatGPT)

### Claude Code (VSCode)
- [ ] Created `.vscode/mcp.json` configuration
- [ ] Added Expedia API key to config
- [ ] Reloaded VSCode window
- [ ] Verified server appears in MCP Servers panel
- [ ] Tested with sample hotel search query

### Claude Desktop
- [ ] Opened config via Settings → Developer → Edit Config
- [ ] Added Expedia MCP configuration
- [ ] Restarted Claude Desktop
- [ ] Verified MCP server is available
- [ ] Tested with sample query

### ChatGPT Desktop
- [ ] Installed Docker Desktop
- [ ] Started Expedia MCP container
- [ ] Installed and configured ngrok
- [ ] Added connector in ChatGPT Settings
- [ ] Tested connection with sample query

### Post-Installation
- [ ] Saved API key securely
- [ ] Added mcp.json to .gitignore (if using git)
- [ ] Tested travel search queries
- [ ] Documented workflow in Trips/CLAUDE.md

---

**Last Updated:** 2025-10-16
