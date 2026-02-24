import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Shield, Activity, ArrowRight } from 'lucide-react';

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans relative overflow-hidden">
            {/* Background Image with Overlay */}
            <div
                className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
                style={{ backgroundImage: "url('/students.png')" }}
            >
                <div className="absolute inset-0 bg-white/85 backdrop-blur-[2px]"></div>
            </div>

            {/* Navbar */}
            <nav className="container mx-auto px-6 py-6 flex items-center justify-between relative z-10">
                <div className="flex items-center gap-3">
                    <div className="bg-blue-600 p-2.5 rounded-xl shadow-lg shadow-blue-500/30">
                        <Mic className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-2xl font-bold tracking-tight text-slate-900">WhisperGuard</span>
                </div>
                <div className="hidden md:flex gap-10 text-sm font-semibold text-slate-600">
                    <a href="#features" className="hover:text-blue-600 transition-colors">Features</a>
                    <a href="#how-it-works" className="hover:text-blue-600 transition-colors">How it works</a>
                </div>
                <button
                    onClick={() => navigate('/dashboard')}
                    className="bg-blue-600 hover:bg-blue-700 px-7 py-3 rounded-full text-white text-sm font-semibold transition-all shadow-lg shadow-blue-500/20"
                >
                    Open Dashboard
                </button>
            </nav>

            {/* Main Content */}
            <main className="container mx-auto px-6 pt-24 pb-32 relative z-10 flex flex-col items-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-blue-100 text-blue-600 text-sm font-bold mb-8 shadow-sm">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-pulse shadow-sm shadow-blue-500" />
                    Real-time AI Audio Analysis
                </div>

                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 text-slate-900 leading-tight text-center max-w-4xl">
                    Detect Whispers <br />
                    <span className="text-blue-600">
                        Maintain Integrity.
                    </span>
                </h1>

                <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto mb-12 font-medium text-center leading-relaxed">
                    Advanced microphone array technology detects localized whispers and anomalies in real-time, ensuring a fair and quiet environment for students.
                </p>

                <button
                    onClick={() => navigate('/dashboard')}
                    className="group bg-blue-600 hover:bg-blue-700 px-10 py-4 rounded-full text-white font-bold text-lg transition-all shadow-xl shadow-blue-600/30 flex items-center justify-center gap-3 mx-auto"
                >
                    Get Started
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>

                {/* Feature Cards below */}
                <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto mt-28 text-left">
                    <div className="bg-white/90 backdrop-blur-xl p-8 rounded-[2rem] shadow-xl shadow-slate-200/50 border border-white/50 hover:shadow-2xl hover:-translate-y-1 transition-all">
                        <div className="bg-blue-50 w-16 h-16 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
                            <Activity className="w-8 h-8 text-blue-600" />
                        </div>
                        <h3 className="text-xl font-bold mb-3 text-slate-900">Real-time Analysis</h3>
                        <p className="text-slate-600 font-medium leading-relaxed">Instantly processes audio to detect voices and measure direction of arrival with high precision.</p>
                    </div>
                    <div className="bg-white/90 backdrop-blur-xl p-8 rounded-[2rem] shadow-xl shadow-slate-200/50 border border-white/50 hover:shadow-2xl hover:-translate-y-1 transition-all">
                        <div className="bg-indigo-50 w-16 h-16 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
                            <Mic className="w-8 h-8 text-indigo-600" />
                        </div>
                        <h3 className="text-xl font-bold mb-3 text-slate-900">DOA Tracking</h3>
                        <p className="text-slate-600 font-medium leading-relaxed">Visually track the exact angle of sound sources in the room to pinpoint the origin.</p>
                    </div>
                    <div className="bg-white/90 backdrop-blur-xl p-8 rounded-[2rem] shadow-xl shadow-slate-200/50 border border-white/50 hover:shadow-2xl hover:-translate-y-1 transition-all">
                        <div className="bg-purple-50 w-16 h-16 rounded-2xl flex items-center justify-center mb-6 shadow-inner">
                            <Shield className="w-8 h-8 text-purple-600" />
                        </div>
                        <h3 className="text-xl font-bold mb-3 text-slate-900">Unobtrusive</h3>
                        <p className="text-slate-600 font-medium leading-relaxed">Works silently in the background, maintaining a calm environment without disrupting students.</p>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default LandingPage;
