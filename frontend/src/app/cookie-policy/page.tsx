'use client'

import React from 'react'
import { ArrowLeft, Cookie } from 'lucide-react'
import Link from 'next/link'
import { motion } from 'framer-motion'

export default function CookiePolicyPage() {
    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans p-6 lg:p-12 selection:bg-orange-500/30">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                className="max-w-4xl mx-auto"
            >
                <div className="flex justify-between items-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-zinc-500 hover:text-zinc-900 transition-colors bg-white shadow-sm px-5 py-3 rounded-full ring-1 ring-zinc-200">
                        <ArrowLeft className="w-4 h-4" /> Back Home
                    </Link>
                </div>

                <div className="bg-white rounded-[2.5rem] p-8 lg:p-14 ring-1 ring-zinc-200/80 shadow-[0_8px_30px_rgba(0,0,0,0.04)] relative overflow-hidden">
                    <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] bg-orange-400/10 rounded-full blur-[100px] pointer-events-none" />

                    <div className="flex flex-col md:flex-row md:items-center gap-6 mb-12 relative z-10 border-b border-zinc-100 pb-10">
                        <div className="w-20 h-20 bg-orange-50 text-orange-500 rounded-3xl flex items-center justify-center ring-1 ring-orange-200 shadow-xl shadow-orange-500/10 shrink-0">
                            <Cookie className="w-10 h-10" />
                        </div>
                        <div>
                            <h1 className="text-4xl lg:text-5xl font-black uppercase tracking-tight text-zinc-900 mb-3">Cookie Policy</h1>
                            <p className="text-xs font-black tracking-widest text-zinc-400 uppercase">Effective Date: October 2026</p>
                        </div>
                    </div>

                    <div className="space-y-6 relative z-10">
                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-orange-500 flex items-center justify-center text-xs">01</span>
                                What Are Cookies and Local Storage?
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                Cookies are small text files placed on your computer or mobile device by websites you visit. Similar technologies, such as HTML5 Local Storage, allow applications to store data directly within your web browser. System Logger PRO primarily relies on Local Storage to manage your session state efficiently and securely.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-orange-500 flex items-center justify-center text-xs">02</span>
                                How We Use These Technologies
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed mb-4">
                                We use Local Storage and strictly necessary cookies exclusively for the following operational purposes:
                            </p>
                            <ul className="list-none space-y-3 text-sm font-medium text-zinc-600">
                                <li className="flex items-start gap-3">
                                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-2 shrink-0" />
                                    <div>
                                        <strong className="text-zinc-800">Authentication & Security:</strong> To store your JSON Web Token (JWT) after a successful login, ensuring that your session remains active and secure as you navigate between dashboard modules.
                                    </div>
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-2 shrink-0" />
                                    <div>
                                        <strong className="text-zinc-800">Functional Preferences:</strong> To remember your UI preferences, such as sidebar toggle states, active tabs, and preferred metric views.
                                    </div>
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-2 shrink-0" />
                                    <div>
                                        <strong className="text-zinc-800">Platform Performance:</strong> To cache non-sensitive initialization data, reducing the load on our backend APIs and improving your overall experience.
                                    </div>
                                </li>
                            </ul>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-orange-500 flex items-center justify-center text-xs">03</span>
                                Zero Third-Party Tracking
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                System Logger PRO is engineered for enterprise-grade privacy. We proudly contain exactly <strong className="text-orange-500">zero</strong> third-party tracking scripts, advertising cookies, or algorithmic analytic trackers. Your navigational behavior within the dashboard is not monetized, shared, or compiled into external marketing profiles.
                            </p>
                            <div className="mt-6 p-4 bg-orange-50/50 rounded-2xl ring-1 ring-orange-200/50">
                                <p className="text-xs font-bold text-orange-700 leading-relaxed text-center">
                                    <span className="uppercase tracking-widest block mb-1">Your data is your data:</span>
                                    We only track what is strictly necessary to securely run the service.
                                </p>
                            </div>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-orange-500 flex items-center justify-center text-xs">04</span>
                                Managing Your Preferences
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                Because the technologies we deploy are strictly necessary for the core functionality and security of the Service, they cannot be completely disabled while using the dashboard. However, you can manually clear your browser's Local Storage or execute the "Logout" function within the application to immediately purge your authentication tokens.
                            </p>
                        </section>

                        <div className="mt-12 pt-8 border-t border-zinc-100 flex flex-wrap gap-4 items-center justify-center">
                            <Link href="/terms-of-service" className="text-xs font-black uppercase tracking-widest text-zinc-400 hover:text-zinc-800 transition-colors px-6 py-3 bg-zinc-50 rounded-full ring-1 ring-zinc-200">
                                Terms of Service &rarr;
                            </Link>
                            <Link href="/privacy-policy" className="text-xs font-black uppercase tracking-widest text-zinc-400 hover:text-zinc-800 transition-colors px-6 py-3 bg-zinc-50 rounded-full ring-1 ring-zinc-200">
                                Privacy Policy &rarr;
                            </Link>
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    )
}
