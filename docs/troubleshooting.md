# AI DJ Troubleshooting Guide

## Common Errors and Solutions

### API Key Errors (401)

#### 1. OPENAI_API_KEY_ERROR
**Error Message:** "OpenAI API key is missing" or "Invalid OpenAI API key format"
**Possible Causes:**
- API key not set in `.env` file
- API key is empty or malformed
- Environment variable not loaded properly

**Solutions:**
1. Check your `.env` file contains: `OPENAI_API_KEY=your_key_here`
2. Verify the API key format on OpenAI dashboard
3. Try restarting the application to reload environment variables
4. Ensure the key has sufficient credits and permissions

#### 2. ELEVENLABS_API_KEY_ERROR
**Error Message:** "ElevenLabs API key is missing"
**Possible Causes:**
- Missing API key in environment variables
- Expired or invalid key

**Solutions:**
1. Add `ELEVENLABS_API_KEY=your_key_here` to `.env`
2. Check key validity on ElevenLabs dashboard
3. Generate a new API key if necessary

### Music Service Errors (503)

#### 1. NAVIDROME_SERVICE_ERROR
**Error Message:** "Error connecting to Navidrome server"
**Possible Causes:**
- Navidrome server is down
- Incorrect server URL
- Authentication failed
- Network connectivity issues

**Solutions:**
1. Verify Navidrome server is running: `http://your-server:4533`
2. Check credentials in `.env`:
   ```
   NAVIDROME_URL=http://your-server:4533
   NAVIDROME_USERNAME=your_username
   NAVIDROME_PASSWORD=your_password
   ```
3. Test network connectivity to the server
4. Check Navidrome server logs for issues

#### 2. SPOTIFY_SERVICE_ERROR
**Error Message:** "Failed to authenticate with Spotify"
**Possible Causes:**
- Invalid client credentials
- Rate limiting
- API scope permissions

**Solutions:**
1. Verify Spotify credentials in `.env`:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```
2. Check API usage limits
3. Review required OAuth scopes
4. Regenerate client credentials if necessary

### File System Errors (500)

#### 1. FILE_SYSTEM_READ_ERROR
**Error Message:** "Error reading now playing data" or "Playlist file not found"
**Possible Causes:**
- Missing required directories
- File permissions issues
- Corrupted data files
- Disk space issues

**Solutions:**
1. Ensure required directories exist:
   ```bash
   mkdir -p logs playlists data
   ```
2. Check file permissions:
   - Windows: Right-click → Properties → Security
   - Linux: `ls -la` and `chmod` if needed
3. Clear corrupted files and let them regenerate
4. Verify sufficient disk space

#### 2. FILE_SYSTEM_WRITE_ERROR
**Error Message:** "Error saving playlist" or "Failed to write log file"
**Possible Causes:**
- Insufficient permissions
- Disk full
- File lock by another process

**Solutions:**
1. Run application with appropriate permissions
2. Free up disk space
3. Check for locked files in Task Manager
4. Verify antivirus isn't blocking writes

### Database Errors

#### 1. DATABASE_CONNECTION_ERROR
**Error Message:** "Failed to connect to database"
**Possible Causes:**
- Database file corrupted
- SQLite version mismatch
- Concurrent access issues

**Solutions:**
1. Backup and recreate database:
   ```bash
   mv data/ai_dj.db data/ai_dj.db.bak
   python server/init_db.py
   ```
2. Check SQLite version compatibility
3. Verify database file permissions
4. Monitor for concurrent access issues

### Network Errors

#### 1. NETWORK_CONNECTION_ERROR
**Error Message:** "Failed to reach external service"
**Possible Causes:**
- Firewall blocking connections
- Proxy configuration issues
- DNS resolution problems
- SSL/TLS errors

**Solutions:**
1. Check firewall settings
2. Configure proxy if needed:
   ```
   HTTP_PROXY=http://your-proxy:port
   HTTPS_PROXY=http://your-proxy:port
   ```
3. Verify DNS resolution
4. Update SSL certificates if needed

## Debugging Tips

### 1. Enable Debug Mode
Set in `.env`:
```
DEBUG_MODE=True
```

### 2. Check Log Files
Important log files:
- `logs/server.log`: Main application logs
- `logs/music_info.log`: Music service interactions
- `logs/file_browser.log`: File system operations

### 3. Common Debug Commands
```bash
# View last 50 lines of server log
tail -n 50 logs/server.log

# Monitor logs in real-time
tail -f logs/server.log

# Check API connectivity
curl http://localhost:5000/api/health

# Test database connection
python server/init_db.py --test
```

### 4. Performance Issues
If experiencing slow performance:
1. Check system resources (CPU, RAM, Disk)
2. Monitor API rate limits
3. Clear cached files in `data/` directory
4. Restart the application

## Getting Help
If issues persist:
1. Check the full error message in logs
2. Note the error code and context
3. Review this troubleshooting guide
4. Search GitHub issues
5. Create a new issue with:
   - Error message and code
   - Log snippets
   - Steps to reproduce
   - Environment details
