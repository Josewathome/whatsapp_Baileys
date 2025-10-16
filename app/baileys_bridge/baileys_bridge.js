const express = require('express');
const makeWASocket = require('@whiskeysockets/baileys').default;
const { useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, Browsers } = require('@whiskeysockets/baileys');
const pino = require('pino');
const { Boom } = require('@hapi/boom');
const fs = require('fs-extra');
const path = require('path');

const app = express();
app.use(express.json());


// Add CORS middleware to handle cross-origin requests
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

// JSON file for session storage
const SESSIONS_FILE = path.join(__dirname, 'whatsapp_sessions.json');

// Enhanced session management with better error handling
class SessionManager {
    constructor() {
        this.activeSockets = new Map();
        this.authenticationCallbacks = new Map();
        this.sessionsData = {};
    }

    async initialize() {
        try {
            await this.loadSessions();
            console.log('✅ Session manager initialized');
        } catch (error) {
            console.error('❌ Session manager initialization failed:', error);
        }
    }

    async loadSessions() {
        try {
            if (await fs.pathExists(SESSIONS_FILE)) {
                const data = await fs.readJson(SESSIONS_FILE);
                this.sessionsData = data;
                console.log(`✅ Loaded ${Object.keys(this.sessionsData).length} sessions from file`);
            } else {
                this.sessionsData = {};
                await this.saveSessions();
                console.log('📁 Created new sessions file');
            }
        } catch (error) {
            console.error('❌ Failed to load sessions file:', error);
            this.sessionsData = {};
        }
    }

    async saveSessions() {
        try {
            await fs.writeJson(SESSIONS_FILE, this.sessionsData, { spaces: 2 });
        } catch (error) {
            console.error('❌ Failed to save sessions file:', error);
        }
    }

    async getAuthState(sessionId) {
        try {
            const { state, saveCreds } = await useMultiFileAuthState(`./auth_info_${sessionId}`);
            
            const enhancedSaveCreds = async () => {
                await saveCreds();
                await this.updateSessionData(sessionId, state);
            };

            if (this.sessionsData[sessionId]) {
                console.log(`📁 Found existing session data for: ${sessionId}`);
            }

            return {
                state,
                saveCreds: enhancedSaveCreds,
                clearState: async () => {
                    await this.clearSessionData(sessionId);
                }
            };
        } catch (error) {
            console.error(`❌ Failed to get auth state for ${sessionId}:`, error);
            throw error;
        }
    }

    async updateSessionData(sessionId, state) {
        this.sessionsData[sessionId] = {
            creds: state.creds,
            keys: state.keys,
            lastUpdated: new Date().toISOString(),
            isAuthenticated: !!state.creds.me
        };
        await this.saveSessions();
    }

    async clearSessionData(sessionId) {
        delete this.sessionsData[sessionId];
        
        try {
            const authDir = `./auth_info_${sessionId}`;
            if (await fs.pathExists(authDir)) {
                await fs.remove(authDir);
                console.log(`🗑️ Removed auth files for session: ${sessionId}`);
            }
        } catch (error) {
            console.error(`❌ Failed to remove auth files for ${sessionId}:`, error);
        }
        
        await this.saveSessions();
    }

    getSessionInfo(sessionId) {
        return this.sessionsData[sessionId] || null;
    }

    addAuthCallback(sessionId, callback) {
        if (!this.authenticationCallbacks.has(sessionId)) {
            this.authenticationCallbacks.set(sessionId, []);
        }
        this.authenticationCallbacks.get(sessionId).push(callback);
    }

    removeAuthCallbacks(sessionId) {
        this.authenticationCallbacks.delete(sessionId);
    }

    notifyAuthCallbacks(sessionId, update) {
        const callbacks = this.authenticationCallbacks.get(sessionId) || [];
        callbacks.forEach(callback => {
            try {
                callback(update);
            } catch (error) {
                console.error('Error in auth callback:', error);
            }
        });
    }

    setSocket(sessionId, socket) {
        this.activeSockets.set(sessionId, socket);
    }

    getSocket(sessionId) {
        return this.activeSockets.get(sessionId);
    }

    removeSocket(sessionId) {
        this.activeSockets.delete(sessionId);
    }

    getAllSessions() {
        return Array.from(this.activeSockets.keys());
    }
}

// Initialize session manager
const sessionManager = new SessionManager();

// Function to convert raw QR code to WhatsApp URL format
function formatQRCode(qrCode) {
    if (!qrCode) return null;
    
    // Remove any existing URL prefixes if present
    const cleanQR = qrCode.replace(/^https:\/\/wa\.me\/settings\/linked_devices#/, '');
    
    // Create the proper WhatsApp QR code URL
    const whatsappQRUrl = `https://wa.me/settings/linked_devices#${cleanQR}`;
    
    console.log(`🔗 Converted QR to WhatsApp URL format`);
    return whatsappQRUrl;
}

// Enhanced connection management with retry logic
async function initSocket(sessionId, retryCount = 0) {
    const maxRetries = 3;
    
    try {
        console.log(`🔄 Initializing socket for session: ${sessionId} (attempt ${retryCount + 1})`);
        
        const { state, saveCreds, clearState } = await sessionManager.getAuthState(sessionId);
        const { version, isLatest } = await fetchLatestBaileysVersion();
        
        console.log(`📱 Using WA v${version.join('.')}, isLatest: ${isLatest}`);

        const sock = makeWASocket({
            version,
            auth: state,
            logger: pino({ level: 'silent' }),
            printQRInTerminal: true,
            browser: Browsers.macOS('Chrome'),
            markOnlineOnConnect: true,
            generateHighQualityLinkPreview: true,
            syncFullHistory: false,
            // Add connection timeout
            connectTimeoutMs: 60000,
            // Keep alive ping
            keepAliveIntervalMs: 30000
        });

        // Enhanced connection event handling
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr, isNewLogin } = update;
            
            console.log(`🔗 [${sessionId}] Connection update:`, connection);

            if (qr) {
                console.log(`📱 [${sessionId}] QR code generated`);
                
                // Convert QR to proper WhatsApp URL format
                const whatsappQRUrl = formatQRCode(qr);
                
                sessionManager.notifyAuthCallbacks(sessionId, { 
                    qr_available: true, 
                    qr_content: qr, // Keep original for backward compatibility
                    qr_url: whatsappQRUrl, // New formatted URL
                    status: 'qr_ready'
                });
            }

            if (connection === 'open') {
                console.log(`✅ [${sessionId}] WhatsApp authenticated successfully!`);
                
                await sessionManager.updateSessionData(sessionId, state);
                
                sessionManager.notifyAuthCallbacks(sessionId, { 
                    authenticated: true,
                    user: sock.user,
                    status: 'authenticated'
                });
                sessionManager.removeAuthCallbacks(sessionId);
            
                // --- Send POST to FastAPI /stop/qrcode ---
                try {
                    const axios = require('axios');
                    const baseUrl = 'http://main-whatsapp-service:8000';  // Loaded from .env.bailey
                    const url = `${baseUrl}/api/v1/stop/qrcode`;
                    axios.post(url, { stop: true }) // non-blocking
                        .then(() => console.log(`📤 Sent stop payload to ${url}`))
                        .catch(err => console.error(`❌ Failed to send stop payload:`, err.message));
                } catch (error) {
                    console.error(`❌ Error sending stop payload:`, error.message);
                }
            }
            
            

            if (connection === 'close') {
                const statusCode = lastDisconnect?.error instanceof Boom 
                    ? lastDisconnect.error.output.statusCode 
                    : null;
                
                console.log(`❌ [${sessionId}] Connection closed. Status code:`, statusCode);
                
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                
                sessionManager.notifyAuthCallbacks(sessionId, { 
                    connection_lost: true, 
                    statusCode,
                    shouldReconnect 
                });

                if (shouldReconnect && retryCount < maxRetries) {
                    const delay = Math.min(1000 * Math.pow(2, retryCount), 30000);
                    console.log(`🔄 [${sessionId}] Attempting to reconnect in ${delay}ms...`);
                    setTimeout(async () => {
                        try {
                            await initSocket(sessionId, retryCount + 1);
                        } catch (error) {
                            console.error(`💥 [${sessionId}] Reconnection failed:`, error);
                        }
                    }, delay);
                } else if (!shouldReconnect) {
                    console.log(`🚫 [${sessionId}] Logged out, cleaning up session...`);
                    await clearState();
                    sessionManager.removeSocket(sessionId);
                    sessionManager.removeAuthCallbacks(sessionId);
                }
            }
        });

        sock.ev.on('creds.update', saveCreds);

        // Handle connection errors
        sock.ev.on('connection.error', (error) => {
            console.error(`💥 [${sessionId}] Connection error:`, error);
        });

        sessionManager.setSocket(sessionId, sock);

        console.log(`🎉 [${sessionId}] Socket initialization complete`);
        return sock;

    } catch (error) {
        console.error(`💥 [${sessionId}] Failed to initialize socket:`, error);
        
        if (retryCount < maxRetries) {
            const delay = Math.min(1000 * Math.pow(2, retryCount), 30000);
            console.log(`🔄 [${sessionId}] Retrying initialization in ${delay}ms...`);
            return new Promise((resolve) => {
                setTimeout(() => {
                    resolve(initSocket(sessionId, retryCount + 1));
                }, delay);
            });
        }
        throw error;
    }
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

// Enhanced start-auth with proper WhatsApp QR code URLs
app.post('/start-auth', async (req, res) => {
    let sessionId = req.body.session_id;
    
    if (!sessionId) {
        return res.status(400).json({ 
            error: 'session_id is required',
            status: 'error'
        });
    }

    console.log(`🔄 Starting auth for session: ${sessionId}`);

    try {
        let sock = sessionManager.getSocket(sessionId);
        
        // Try to restore existing session
        const sessionInfo = sessionManager.getSessionInfo(sessionId);
        if (sessionInfo && sessionInfo.isAuthenticated && !sock) {
            try {
                sock = await initSocket(sessionId);
            } catch (error) {
                console.log(`🔄 Failed to restore session, starting fresh:`, error.message);
            }
        }
        
        // Initialize new socket if needed
        if (!sock) {
            sock = await initSocket(sessionId);
        }

        // Check if already authenticated
        if (sock.user) {
            return res.json({
                authenticated: true,
                session_id: sessionId,
                status: 'already_authenticated',
                user: sock.user
            });
        }

        // Wait for QR code with timeout
        const authResult = await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('QR code generation timeout (50 seconds)'));
            }, 50000);

            sessionManager.addAuthCallback(sessionId, (update) => {
                if (update.authenticated) {
                    clearTimeout(timeout);
                    resolve({
                        authenticated: true,
                        status: 'authenticated',
                        user: update.user
                    });
                } else if (update.qr_available) {
                    clearTimeout(timeout);
                    resolve({
                        qr_content: update.qr_content, // Original QR
                        qr_url: update.qr_url,         // Formatted WhatsApp URL
                        status: 'qr_ready'
                    });
                } else if (update.connection_lost) {
                    clearTimeout(timeout);
                    reject(new Error(`Connection lost: ${update.statusCode}`));
                }
            });
        });

        res.json({
            ...authResult,
            session_id: sessionId
        });

    } catch (error) {
        console.error('Error in /start-auth:', error);
        sessionManager.removeAuthCallbacks(sessionId);
        
        res.status(500).json({ 
            error: error.message,
            status: 'error'
        });
    }
});

// QR Code formatting endpoint - for manual QR conversion if needed
app.post('/format-qr', (req, res) => {
    try {
        const { qr_content } = req.body;
        
        if (!qr_content) {
            return res.status(400).json({ 
                error: 'qr_content is required',
                status: 'error'
            });
        }

        const formattedQR = formatQRCode(qr_content);
        
        res.json({
            original_qr: qr_content,
            formatted_qr: formattedQR,
            status: 'success',
            message: 'QR code formatted for WhatsApp'
        });

    } catch (error) {
        console.error('Error in /format-qr:', error);
        res.status(500).json({ 
            error: error.message,
            status: 'error'
        });
    }
});

// Check authentication status
app.post('/check-auth', async (req, res) => {
    try {
        const { session_id } = req.body;
        
        if (!session_id) {
            return res.status(400).json({ 
                error: 'session_id is required',
                status: 'error'
            });
        }

        const sock = sessionManager.getSocket(session_id);
        const isAuthenticated = sock && sock.user;

        res.json({
            authenticated: isAuthenticated,
            session_id: session_id,
            status: isAuthenticated ? 'authenticated' : 'not_authenticated',
            has_qr: !isAuthenticated,
            user: sock?.user || null
        });

    } catch (error) {
        console.error('Error in /check-auth:', error);
        res.status(500).json({ 
            error: error.message,
            status: 'error'
        });
    }
});

// Health check - Enhanced with more details
app.get('/health', (req, res) => {
    const sessions = sessionManager.getAllSessions();
    const totalSessions = sessions.length;
    const authenticatedSessions = sessions.filter(sessionId => {
        const sock = sessionManager.getSocket(sessionId);
        return sock && sock.user;
    }).length;
    
    res.json({ 
        status: 'healthy',
        bridge_status: totalSessions > 0 ? 'connected' : 'disconnected',
        authenticated: authenticatedSessions > 0,
        has_qr: totalSessions > authenticatedSessions,
        total_sessions: totalSessions,
        authenticated_sessions: authenticatedSessions,
        timestamp: new Date().toISOString()
    });
});

// Test endpoint to verify bridge is working
app.get('/test', (req, res) => {
    res.json({ 
        message: 'Baileys bridge is running!',
        status: 'ok',
        timestamp: new Date().toISOString()
    });
});

// Preserve all your original endpoints (onWhatsApp, fetchStatus, getBusinessProfile, profilePictureUrl)
app.post('/onWhatsApp', async (req, res) => {
    try {
        const { session_id, jid } = req.body;
        
        if (!session_id || !jid) {
            return res.status(400).json({ 
                error: 'session_id and jid are required',
                status: 'error'
            });
        }

        const sock = sessionManager.getSocket(session_id);
        
        if (!sock) {
            return res.status(404).json({ 
                error: 'Session not found or inactive',
                status: 'error'
            });
        }

        if (!sock.user) {
            return res.status(401).json({ 
                error: 'WhatsApp not authenticated for this session',
                status: 'error'
            });
        }

        const result = await sock.onWhatsApp(jid);
        res.json(result);

    } catch (error) {
        console.error('Error in /onWhatsApp:', error);
        res.status(500).json({ 
            error: error.message,
            status: 'error'
        });
    }
});

app.post('/fetchStatus', async (req, res) => {
    try {
        const { session_id, jid } = req.body;
        
        if (!session_id || !jid) {
            return res.status(400).json({ 
                error: 'session_id and jid are required',
                status: 'error'
            });
        }

        const sock = sessionManager.getSocket(session_id);
        
        if (!sock) {
            return res.status(404).json({ 
                error: 'Session not found or inactive',
                status: 'error'
            });
        }

        if (!sock.user) {
            return res.status(401).json({ 
                error: 'WhatsApp not authenticated for this session',
                status: 'error'
            });
        }

        const result = await sock.fetchStatus(jid);
        res.json(result);

    } catch (error) {
        console.error('Error in /fetchStatus:', error);
        res.status(500).json({ 
            error: error.message,
            status: 'error'
        });
    }
});


app.post('/getBusinessProfile', async (req, res) => {
    try {
        const { session_id, jid } = req.body;
        
        if (!session_id || !jid) {
            return res.status(400).json({ 
                error: 'session_id and jid are required',
                status: 'error'
            });
        }

        const sock = sessionManager.getSocket(session_id);
        
        if (!sock) {
            return res.status(404).json({ 
                error: 'Session not found or inactive',
                status: 'error'
            });
        }

        if (!sock.user) {
            return res.status(401).json({ 
                error: 'WhatsApp not authenticated for this session',
                status: 'error'
            });
        }

        let result = await sock.getBusinessProfile(jid);

        // Fabricate mock payload if empty
        if (!result || (typeof result === 'object' && Object.keys(result).length === 0)) {
            result = { is_business: false };
        }

        res.json(result);

    } catch (error) {
        console.error('Error in /getBusinessProfile:', error);
        res.status(500).json({ 
            error: error.message,
            status: 'error'
        });
    }
});


app.post('/profilePictureUrl', async (req, res) => {
    try {
        const { session_id, jid, format } = req.body;
        
        if (!session_id || !jid) {
            return res.status(400).json({ 
                error: 'session_id and jid are required',
                status: 'error'
            });
        }

        const sock = sessionManager.getSocket(session_id);
        
        if (!sock) {
            return res.status(404).json({ 
                error: 'Session not found or inactive',
                status: 'error'
            });
        }

        if (!sock.user) {
            return res.status(401).json({ 
                error: 'WhatsApp not authenticated for this session',
                status: 'error'
            });
        }

        const url = await sock.profilePictureUrl(jid, format);
        res.json({ url });

    } catch (error) {
        console.error('Error in /profilePictureUrl:', error);
        res.status(500).json({ 
            error: error.message,
            status: 'error'
        });
    }
});

const PORT = 3000;
const HOST = '0.0.0.0';

// Enhanced startup with proper initialization
async function startServer() {
    try {
        // Initialize session manager first
        await sessionManager.initialize();
        
        // Start the server
        const server = app.listen(PORT, HOST, () => {
            console.log(`🚀 Enhanced Baileys bridge listening on ${HOST}:${PORT}`);
            console.log(`📱 Ready for multiple WhatsApp sessions`);
            console.log(`💾 Storage: JSON File`);
            console.log(`🔗 Health check: http://${HOST}:${PORT}/health`);
            console.log(`🧪 Test endpoint: http://${HOST}:${PORT}/test`);
            console.log(`✅ QR codes are now formatted for WhatsApp!`);
            console.log(`✅ Server started successfully!`);
        });

        // Handle server errors
        server.on('error', (error) => {
            if (error.code === 'EADDRINUSE') {
                console.error(`❌ Port ${PORT} is already in use`);
                process.exit(1);
            } else {
                console.error('❌ Server error:', error);
            }
        });

        // Verify server is responding
        server.on('listening', () => {
            console.log(`✅ Server is listening and ready for connections`);
        });

    } catch (error) {
        console.error('💥 Failed to start Baileys bridge:', error);
        process.exit(1);
    }
}

// Enhanced graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down gracefully...');
    
    const sessions = sessionManager.getAllSessions();
    console.log(`🔄 Closing ${sessions.length} active sessions...`);
    
    for (const sessionId of sessions) {
        const sock = sessionManager.getSocket(sessionId);
        if (sock) {
            try {
                await sock.end();
                console.log(`✅ Closed session: ${sessionId}`);
            } catch (error) {
                console.error(`❌ Error closing session ${sessionId}:`, error);
            }
        }
    }
    
    console.log('✅ Cleanup complete');
    process.exit(0);
});

process.on('uncaughtException', (error) => {
    console.error('💥 Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
});

// Start the server
startServer().catch(console.error);