import React from 'react';
import { AlertTriangle, X, Compass } from 'lucide-react';

const WhisperAlert = ({ alerts, onDismiss }) => {
    return (
        <div className="fixed top-6 right-6 z-50 flex flex-col gap-3 pointer-events-none" style={{ maxWidth: '400px' }}>
            {alerts.map((alert) => (
                <div
                    key={alert.id}
                    className="pointer-events-auto whisper-alert-enter bg-gradient-to-r from-red-600 to-amber-500 text-white rounded-2xl shadow-2xl shadow-red-500/30 px-5 py-4 flex items-start gap-4 border border-red-400/30 backdrop-blur-sm"
                    style={{ animation: alert.dismissing ? 'whisperAlertExit 0.4s ease-in forwards' : 'whisperAlertEnter 0.5s ease-out forwards' }}
                >
                    {/* Icon */}
                    <div className="flex-shrink-0 mt-0.5">
                        <div className="bg-white/20 rounded-xl p-2">
                            <AlertTriangle className="w-5 h-5 text-white" />
                        </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                        <div className="font-bold text-sm tracking-wide mb-1">⚠️ Whisper Detected!</div>
                        <div className="flex items-center gap-2 text-white/90 text-sm font-medium">
                            <Compass className="w-4 h-4 flex-shrink-0" />
                            <span>Check DOA: <span className="font-extrabold text-white">{alert.doa}°</span></span>
                        </div>
                        <div className="text-white/60 text-xs mt-1.5">
                            {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}
                        </div>
                    </div>

                    {/* Dismiss Button */}
                    <button
                        onClick={() => onDismiss(alert.id)}
                        className="flex-shrink-0 hover:bg-white/20 rounded-lg p-1 transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>

                    {/* Auto-dismiss progress bar */}
                    <div className="absolute bottom-0 left-0 right-0 h-1 rounded-b-2xl overflow-hidden">
                        <div
                            className="h-full bg-white/40 rounded-b-2xl"
                            style={{ animation: 'whisperProgressShrink 5s linear forwards' }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
};

export default WhisperAlert;
