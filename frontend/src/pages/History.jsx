import React, { useState, useEffect } from 'react';
import { History as HistoryIcon, Search, Calendar, Filter, AlertTriangle, CheckCircle2 } from 'lucide-react';

const mockHistory = [
    { id: 1, date: '2026-02-24', time: '10:15 AM', duration: '12s', doa: 45, status: 'Resolved' },
    { id: 2, date: '2026-02-24', time: '11:02 AM', duration: '5s', doa: 120, status: 'Needs Review' },
    { id: 3, date: '2026-02-23', time: '02:30 PM', duration: '25s', doa: 310, status: 'Resolved' },
    { id: 4, date: '2026-02-23', time: '03:45 PM', duration: '8s', doa: 90, status: 'Resolved' },
    { id: 5, date: '2026-02-22', time: '09:10 AM', duration: '15s', doa: 180, status: 'Resolved' },
];

const History = () => {
    const [events, setEvents] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        // Load from local storage or use mock
        const savedHistory = JSON.parse(localStorage.getItem('whisperHistory')) || mockHistory;
        setEvents(savedHistory);

        // Listen for new events added by the Dashboard (if any)
        const handleNewEvent = () => {
            const updatedHistory = JSON.parse(localStorage.getItem('whisperHistory')) || mockHistory;
            setEvents(updatedHistory);
        };
        window.addEventListener('historyUpdated', handleNewEvent);
        return () => window.removeEventListener('historyUpdated', handleNewEvent);
    }, []);

    const filteredEvents = events.filter(event =>
        event.date.includes(searchTerm) || event.time.includes(searchTerm) || event.status.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="flex bg-[#f3f4f6] min-h-screen font-sans text-slate-800">
            <main className="flex-1 p-8 overflow-y-auto">
                <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Detection History</h1>
                        <p className="text-slate-500 mt-1">Review past whisper detection events and anomalies.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
                            <Calendar className="w-4 h-4" />
                            Date Range
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-indigo-50 border border-indigo-100 rounded-xl shadow-sm text-sm font-medium text-indigo-600 hover:bg-indigo-100 transition-colors">
                            <Filter className="w-4 h-4" />
                            Filters
                        </button>
                    </div>
                </header>

                <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                    {/* Search Bar */}
                    <div className="p-6 border-b border-slate-100">
                        <div className="relative max-w-md">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Search className="w-5 h-5 text-slate-400" />
                            </div>
                            <input
                                type="text"
                                placeholder="Search by date, time, or status..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="block w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400"
                            />
                        </div>
                    </div>

                    {/* Desktop Table View */}
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-50 border-b border-slate-100">
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date & Time</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Direction (DOA)</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Duration</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {filteredEvents.map((event) => (
                                    <tr key={event.id} className="hover:bg-slate-50/80 transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-slate-900">{event.date}</div>
                                            <div className="text-sm text-slate-500">{event.time}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center border border-indigo-100">
                                                    <span className="text-xs font-bold text-indigo-600">{event.doa}°</span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm font-medium text-slate-700 bg-slate-100 px-3 py-1 rounded-lg">
                                                {event.duration}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            {event.status === 'Resolved' ? (
                                                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-600 text-xs font-medium border border-emerald-100">
                                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                                    Resolved
                                                </div>
                                            ) : (
                                                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-50 text-orange-600 text-xs font-medium border border-orange-100">
                                                    <AlertTriangle className="w-3.5 h-3.5" />
                                                    Needs Review
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button className="text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100">
                                                View Details
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>

                        {filteredEvents.length === 0 && (
                            <div className="p-12 text-center text-slate-500 flex flex-col items-center">
                                <HistoryIcon className="w-12 h-12 text-slate-300 mb-4" />
                                <p className="text-lg font-medium text-slate-700">No events found.</p>
                                <p className="text-sm mt-1">Try adjusting your search or filters.</p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default History;
