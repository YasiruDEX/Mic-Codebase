import React, { useState, useEffect } from 'react';
import { Save, User, Image as ImageIcon } from 'lucide-react';

const Settings = () => {
    const [name, setName] = useState('');
    const [handle, setHandle] = useState('');
    const [profileImage, setProfileImage] = useState('');
    const [saveStatus, setSaveStatus] = useState('');

    useEffect(() => {
        // Load existing settings
        const savedName = localStorage.getItem('profileName') || 'Main Supervisor';
        const savedHandle = localStorage.getItem('profileHandle') || '@supervisor_1';
        const savedImage = localStorage.getItem('profileImage') || 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin1';

        setName(savedName);
        setHandle(savedHandle);
        setProfileImage(savedImage);
    }, []);

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setProfileImage(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSave = () => {
        localStorage.setItem('profileName', name);
        localStorage.setItem('profileHandle', handle);
        localStorage.setItem('profileImage', profileImage);
        setSaveStatus('Settings saved successfully!');

        // Trigger a custom event so the Sidebar can update immediately
        window.dispatchEvent(new Event('profileUpdated'));

        setTimeout(() => setSaveStatus(''), 3000);
    };

    return (
        <div className="flex bg-[#f3f4f6] min-h-screen font-sans text-slate-800">
            <main className="flex-1 p-8 overflow-y-auto">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Settings</h1>
                    <p className="text-slate-500 mt-1">Manage your account preferences and profile details.</p>
                </header>

                <div className="max-w-2xl bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
                    <div className="mb-8">
                        <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                            <User className="w-5 h-5 text-indigo-500" />
                            Profile Details
                        </h2>

                        <div className="space-y-6">
                            {/* Profile Image Preview */}
                            <div className="flex items-center gap-6">
                                <img
                                    src={profileImage}
                                    alt="Profile Preview"
                                    className="w-24 h-24 rounded-full bg-slate-100 object-cover border-4 border-slate-50 shadow-sm"
                                />
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">Profile Image</label>
                                    <div className="flex items-center gap-2">
                                        <label className="cursor-pointer bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2">
                                            <ImageIcon className="w-4 h-4" />
                                            Choose Image
                                            <input
                                                type="file"
                                                accept="image/*"
                                                onChange={handleImageChange}
                                                className="hidden"
                                            />
                                        </label>
                                    </div>
                                    <p className="text-xs text-slate-500 mt-2">Recommended size: 256x256px. Max 2MB.</p>
                                </div>
                            </div>

                            {/* Name Input */}
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">Display Name</label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                                    placeholder="Enter your name"
                                />
                            </div>

                            {/* Handle Input */}
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">Username Handle</label>
                                <input
                                    type="text"
                                    value={handle}
                                    onChange={(e) => setHandle(e.target.value)}
                                    className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                                    placeholder="@username"
                                />
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between">
                            {saveStatus ? (
                                <span className="text-emerald-500 text-sm font-medium bg-emerald-50 px-3 py-1.5 rounded-lg">
                                    {saveStatus}
                                </span>
                            ) : <div></div>}
                            <button
                                onClick={handleSave}
                                className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl font-medium shadow-lg shadow-indigo-600/20 transition-all flex items-center gap-2"
                            >
                                <Save className="w-4 h-4" />
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Settings;
