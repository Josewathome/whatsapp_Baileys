// app/baileys_bridge/baileys_bridge.js (ENHANCED WITH OUR API)
const express = require('express');
const makeWASocket = require('@whiskeysockets/baileys').default;
const { useMultiFileAuthState } = require('@whiskeysockets/baileys');
const pino = require('pino');

const app = express();
app.use(express.json());

let sock = null;
let currentQR = null;
let isAuthenticated = false;
let authenticationCallbacks = new Map();

// Initialize connection
async function initSocket() {
    try {
        const { state, saveCreds } = await useMultiFileAuthState('./auth_info');
        
        sock = makeWASocket({
            auth: state,
            logger: pino({ level: 'silent' }),
            printQRInTerminal: true
        });
        
        // Handle QR code generation
        sock.ev.on('connection.update', (update) => {
            const { connection, qr } = update;
            console.log('   Connection update:', connection);
            
            if (qr) {
                console.log('🔄 New QR code generated');
                currentQR = qr;
                isAuthenticated = false;
                
                // Notify all waiting sessions
                authenticationCallbacks.forEach((callback) => {
                    callback({ qr_available: true });
                });
            }
            
            if (connection === 'open') {
                console.log('  WhatsApp authenticated successfully!');
                isAuthenticated = true;
                currentQR = null;
                
                // Notify all waiting sessions
                authenticationCallbacks.forEach((callback) => {
                    callback({ authenticated: true });
                });
                authenticationCallbacks.clear();
            }
            
            if (connection === 'close') {
                console.log('   WhatsApp connection closed');
                isAuthenticated = false;
                currentQR = null;
            }
        });
        
        sock.ev.on('creds.update', saveCreds);
        
        console.log('  Baileys socket initialized');
    } catch (error) {
        console.error('   Failed to initialize Baileys:', error);
        throw error;
    }
}

// Start authentication and get QR code
app.post('/start-auth', async (req, res) => {
    try {
        const { session_id } = req.body;
        console.log(`🔄 Starting auth for session: ${session_id}`);
        
        if (!sock) {
            await initSocket();
        }
        
        // If already authenticated, return immediately
        if (isAuthenticated) {
            return res.json({
                authenticated: true,
                session_id: session_id,
                status: 'already_authenticated'
            });
        }
        
        // If QR code is available, return it
        if (currentQR) {
            console.log(`📱 Returning QR code for session: ${session_id}`);
            return res.json({
                qr_content: currentQR,
                session_id: session_id,
                status: 'qr_ready'
            });
        }
        
        // Wait for QR code (max 10 seconds)
        const waitForQR = new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('QR code generation timeout'));
            }, 50000);
            
            authenticationCallbacks.set(session_id, (update) => {
                if (update.qr_available && currentQR) {
                    clearTimeout(timeout);
                    resolve(currentQR);
                }
            });
        });
        
        const qrContent = await waitForQR;
        authenticationCallbacks.delete(session_id);
        
        res.json({
            qr_content: qrContent,
            session_id: session_id,
            status: 'qr_ready'
        });
        
    } catch (error) {
        console.error('Error in /start-auth:', error);
        authenticationCallbacks.delete(req.body.session_id);
        res.status(500).json({ error: error.message });
    }
});

// Check authentication status
app.post('/check-auth', async (req, res) => {
    try {
        const { session_id } = req.body;
        
        res.json({
            authenticated: isAuthenticated,
            session_id: session_id,
            status: isAuthenticated ? 'authenticated' : 'not_authenticated',
            has_qr: !!currentQR
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: sock ? 'connected' : 'disconnected',
        authenticated: isAuthenticated,
        has_qr: !!currentQR
    });
});

// Check if number exists on WhatsApp
app.post('/onWhatsApp', async (req, res) => {
    try {
        const { jid } = req.body;
        if (!isAuthenticated) {
            return res.status(401).json({ error: 'WhatsApp not authenticated' });
        }
        const result = await sock.onWhatsApp(jid);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Fetch status
app.post('/fetchStatus', async (req, res) => {
    try {
        const { jid } = req.body;
        if (!isAuthenticated) {
            return res.status(401).json({ error: 'WhatsApp not authenticated' });
        }
        const result = await sock.fetchStatus(jid);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get business profile
app.post('/getBusinessProfile', async (req, res) => {
    try {
        const { jid } = req.body;
        if (!isAuthenticated) {
            return res.status(401).json({ error: 'WhatsApp not authenticated' });
        }
        const result = await sock.getBusinessProfile(jid);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get profile picture URL
app.post('/profilePictureUrl', async (req, res) => {
    try {
        const { jid, format } = req.body;
        if (!isAuthenticated) {
            return res.status(401).json({ error: 'WhatsApp not authenticated' });
        }
        const url = await sock.profilePictureUrl(jid, format);
        res.json({ url });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

const PORT = 3000;

// Initialize on startup
initSocket().then(() => {
    app.listen(PORT, () => {
        console.log(`  Baileys bridge listening on port ${PORT}`);
        console.log(` Ready for REAL WhatsApp authentication`);
    });
}).catch(error => {
    console.error('   Failed to start Baileys bridge:', error);
    process.exit(1);
});