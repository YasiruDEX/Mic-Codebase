import React, { useEffect, useState, useRef, useCallback } from 'react';
import { ref, onValue } from 'firebase/database';
import { db } from '../firebase';
import WhisperAlert from '../components/WhisperAlert';
import { Mic, Activity, AlertTriangle, AlertCircle, History, AudioLines } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid } from 'recharts';

// Short beep alert sound as base64 data URI (a simple notification tone)
const ALERT_SOUND_URL = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgkKuyl2Y3I0qBq7OscU07S4Kqsqtvb293hIeEeWxqcHyMl5iSfWRfbICZpZ+MbVRUaYORnJJ8YVJdfJOgo5V+YFhkfZWkpp2JcmJoe5SnqaKQfHJwfpOeop2UiYODhYeHhIF7eHd4fICEhoiHhIN/fXx8foCCg4SEg4KAgIGBgoOEhISEg4OCg4OEhIWFhYWEhISEhIWFhYWFhYWFhYWFhYaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaG';

const MAX_VISIBLE_ALERTS = 5;
const ALERT_AUTO_DISMISS_MS = 5000;

const Dashboard = () => {
    const [micData, setMicData] = useState({ doa: 0, is_voice: false, timestamp: 0 });
    const [history, setHistory] = useState([]);
    const [whisperCount, setWhisperCount] = useState(0);
    const [alerts, setAlerts] = useState([]);
    const prevVoiceRef = useRef(false);
    const alertIdCounter = useRef(0);

    // Request browser notification permission on mount
    useEffect(() => {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }, []);

    // Play alert beep
    const playAlertSound = useCallback(() => {
        try {
            const audio = new Audio(ALERT_SOUND_URL);
            audio.volume = 0.6;
            audio.play().catch(() => { /* ignore autoplay restrictions */ });
        } catch (e) {
            // silently fail
        }
    }, []);

    // Fire browser notification
    const fireBrowserNotification = useCallback((doa) => {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification('⚠️ Whisper Detected!', {
                body: `Check DOA: ${doa}°\nA whisper has been detected in the classroom.`,
                icon: '🎤',
                tag: 'whisper-alert',
                requireInteraction: false,
            });
            setTimeout(() => notification.close(), 6000);
        }
    }, []);

    // Dismiss an alert
    const dismissAlert = useCallback((id) => {
        setAlerts(prev => prev.map(a => a.id === id ? { ...a, dismissing: true } : a));
        setTimeout(() => {
            setAlerts(prev => prev.filter(a => a.id !== id));
        }, 400);
    }, []);

    // Push a new whisper alert
    const pushAlert = useCallback((doa, timestamp) => {
        const id = ++alertIdCounter.current;
        const newAlert = { id, doa, timestamp, dismissing: false };

        setAlerts(prev => {
            const updated = [newAlert, ...prev];
            return updated.slice(0, MAX_VISIBLE_ALERTS);
        });

        setTimeout(() => dismissAlert(id), ALERT_AUTO_DISMISS_MS);
        playAlertSound();
        fireBrowserNotification(doa);
    }, [dismissAlert, playAlertSound, fireBrowserNotification]);

    useEffect(() => {
        const micDataRef = ref(db, 'mic_data');

        const unsubscribe = onValue(micDataRef, (snapshot) => {
            const data = snapshot.val();
            if (data) {
                setMicData(data);

                setHistory(prev => {
                    const newHistory = [...prev, {
                        ...data,
                        voiceValue: data.is_voice ? 1 : 0,
                        time: new Date(data.timestamp).toLocaleTimeString([], { hour12: false, second: '2-digit', minute: '2-digit' })
                    }];
                    return newHistory.slice(-30);
                });

                if (data.is_voice) {
                    setWhisperCount(prev => prev + 1);
                }

                // Edge detection: only trigger alert on false → true transition
                if (data.is_voice && !prevVoiceRef.current) {
                    pushAlert(data.doa, data.timestamp);
                }

                prevVoiceRef.current = data.is_voice;
            }
        });

        return () => unsubscribe();
    }, [pushAlert]);

    return (
        <div className="flex bg-[#f3f4f6] min-h-screen font-sans text-slate-800">
            {/* Whisper Alert Toasts */}
            <WhisperAlert alerts={alerts} onDismiss={dismissAlert} />

            {/* Main Content Area */}
            <main className="flex-1 p-8 overflow-y-auto">
                <header className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Monitoring Dashboard</h1>
                        <p className="text-slate-500 mt-1">Real-time analysis from ReSpeaker Mic Array.</p>
                    </div>
                    <div className="flex items-center gap-4 bg-white px-4 py-2 rounded-2xl shadow-sm border border-slate-100">
                        <div className={`w-3 h-3 rounded-full ${micData.is_voice ? 'bg-red-500 animate-pulse' : 'bg-emerald-500'}`}></div>
                        <span className="text-sm font-semibold">{micData.is_voice ? 'Voice Detected' : 'Monitoring Active'}</span>
                    </div>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    {/* DOA Widget */}
                    <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 flex flex-col items-center justify-center relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4">
                            <AudioLines className="w-5 h-5 text-slate-400" />
                        </div>
                        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-6">Direction of Arrival</h2>

                        {/* Visual Compass */}
                        <div className="relative w-40 h-40 rounded-full border-8 border-slate-50 flex items-center justify-center shadow-inner mb-4">
                            <div className="w-4 h-4 rounded-full bg-indigo-500 z-10 shadow-lg" />
                            <div
                                className="absolute w-1 h-20 bg-gradient-to-t from-indigo-500 to-transparent origin-bottom left-1/2 -ml-[2px] top-0 transition-transform duration-300 ease-out"
                                style={{ transform: `rotate(${micData.doa}deg)` }}
                            />
                            <span className="absolute top-2 text-xs font-medium text-slate-400">0°</span>
                            <span className="absolute bottom-2 text-xs font-medium text-slate-400">180°</span>
                            <span className="absolute right-2 text-xs font-medium text-slate-400">90°</span>
                            <span className="absolute left-2 text-xs font-medium text-slate-400">270°</span>
                        </div>

                        <div className="text-4xl font-extrabold text-indigo-600 tracking-tighter">
                            {micData.doa}°
                        </div>
                    </div>

                    {/* Status Widget */}
                    <div className="bg-gradient-to-b from-[#1e2029] to-[#15161c] text-white rounded-3xl p-6 shadow-xl relative overflow-hidden group">
                        <div className="absolute -right-6 -top-6 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-all"></div>

                        <div className="flex items-center justify-between mb-8">
                            <h2 className="text-sm font-medium tracking-wider text-slate-400">Audio Status</h2>
                            <div className="p-2 bg-indigo-500/20 rounded-xl">
                                <Activity className="w-5 h-5 text-indigo-400" />
                            </div>
                        </div>

                        <div className="mt-auto">
                            <div className="flex items-baseline gap-2 mb-2">
                                <span className="text-5xl font-black">{micData.is_voice ? 'Active' : 'Silence'}</span>
                            </div>
                            <p className="text-slate-400 text-sm flex items-center gap-2">
                                {micData.is_voice ? (
                                    <span className="flex items-center gap-1 text-red-400"><AlertCircle className="w-4 h-4" /> Signal captured</span>
                                ) : (
                                    <span className="flex items-center gap-1 text-emerald-400">Environment clear</span>
                                )}
                            </p>
                        </div>
                    </div>

                    {/* Metrics Widget */}
                    <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 flex flex-col justify-between">
                        <div className="flex items-center justify-between">
                            <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Detection Events</h2>
                            <div className="p-2 bg-red-50 text-red-500 rounded-xl">
                                <AlertTriangle className="w-5 h-5" />
                            </div>
                        </div>

                        <div className="mt-6">
                            <div className="text-5xl font-black text-slate-800 tracking-tighter mb-2">{whisperCount}</div>
                            <div className="text-sm font-medium text-red-500 bg-red-50 px-3 py-1.5 rounded-lg inline-block">
                                Cumulative whispers detected
                            </div>
                        </div>

                        <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-sm">
                            <span className="text-slate-500">Since tracking started</span>
                            <span className="font-semibold text-indigo-600 cursor-pointer hover:underline">Reset</span>
                        </div>
                    </div>
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* History Chart */}
                    <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-100 h-[350px] flex flex-col">
                        <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                            <History className="w-5 h-5 text-slate-400" /> DOA Timeline
                        </h2>
                        <div className="h-64 w-full relative">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={history}>
                                    <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#94a3b8' }} dy={10} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 360]} />
                                    <Tooltip
                                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="doa"
                                        stroke="#6366f1"
                                        strokeWidth={3}
                                        dot={false}
                                        activeDot={{ r: 6, fill: '#6366f1', strokeWidth: 0 }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Voice Activity Chart */}
                    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col relative h-[350px]">
                        <div className="flex items-center justify-between mb-2 z-10">
                            <h3 className="text-slate-700 font-medium">Voice Activity Tracker</h3>
                            <button className="text-blue-500 text-sm font-medium border border-blue-50 px-5 py-1.5 rounded-full hover:bg-blue-50/50 transition-colors">Details</button>
                        </div>
                        <div className="flex-1 w-full mt-4">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="colorVoice" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#0d6efd" stopOpacity={0.15} />
                                            <stop offset="95%" stopColor="#0d6efd" stopOpacity={0} />
                                        </linearGradient>
                                        <filter id="shadow" height="200%">
                                            <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#0d6efd" floodOpacity="0.2" />
                                        </filter>
                                    </defs>
                                    <CartesianGrid vertical={false} stroke="#f1f5f9" />
                                    <XAxis dataKey="time" axisLine={{ stroke: '#f8fafc' }} tickLine={false} tick={{ fontSize: 11, fill: '#94a3b8' }} dy={10} />
                                    <YAxis
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 11, fill: '#94a3b8' }}
                                        domain={[0, 1]}
                                        tickFormatter={(value) => value === 1 ? 'Voice' : 'Silence'}
                                    />
                                    <Tooltip
                                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                        formatter={(value, name, props) => props.payload.is_voice ? 'Voice Detected' : 'Silence'}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="voiceValue"
                                        stroke="#0d6efd"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#colorVoice)"
                                        animationDuration={300}
                                        activeDot={{ r: 6, strokeWidth: 2, stroke: '#fff', fill: '#0d6efd' }}
                                        style={{ filter: 'url(#shadow)' }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

            </main>
        </div>
    );
};

export default Dashboard;
