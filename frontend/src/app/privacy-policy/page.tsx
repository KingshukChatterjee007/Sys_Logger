'use client'

import React from 'react'
import { ArrowLeft, Shield } from 'lucide-react'
import Link from 'next/link'
import { motion } from 'framer-motion'

export default function PrivacyPolicyPage() {
    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans p-6 lg:p-12 selection:bg-emerald-500/30">
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
                    <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] bg-emerald-400/10 rounded-full blur-[100px] pointer-events-none" />

                    <div className="flex flex-col md:flex-row md:items-center gap-6 mb-12 relative z-10 border-b border-zinc-100 pb-10">
                        <div className="w-20 h-20 bg-emerald-50 text-emerald-500 rounded-3xl flex items-center justify-center ring-1 ring-emerald-200 shadow-xl shadow-emerald-500/10 shrink-0">
                            <Shield className="w-10 h-10" />
                        </div>
                        <div>
                            <h1 className="text-4xl lg:text-5xl font-black uppercase tracking-tight text-zinc-900 mb-3">Privacy Policy</h1>
                            <p className="text-xs font-black tracking-widest text-zinc-400 uppercase">Effective Date: October 2026</p>
                        </div>
                    </div>

                    <div className="space-y-6 relative z-10">
                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-emerald-500 flex items-center justify-center text-xs">01</span>
                                Introduction and Scope
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                Welcome to System Logger PRO. This Privacy Policy ("Policy") outlines how we collect, use, protect, and disclose your information when you use our monitoring service, website, and related applications (collectively, the "Service"). We are committed to ensuring that your privacy is protected and that your data is handled transparently and securely.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-emerald-500 flex items-center justify-center text-xs">02</span>
                                Information We Collect
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed mb-4">
                                We collect specific types of information to provide and improve the Service:
                            </p>
                            <ul className="list-disc list-inside space-y-2 text-sm font-medium text-zinc-600 marker:text-emerald-500 ml-2">
                                <li><strong className="text-zinc-800">Account Information:</strong> When you register an organization, we collect your organization name, contact email, and cryptographic password hashes.</li>
                                <li><strong className="text-zinc-800">System Telemetry Data:</strong> Our strictly scoped client agents collect hardware performance metrics, including CPU load, RAM allocation, GPU compute load, and network Rx/Tx rates.</li>
                                <li><strong className="text-zinc-800">Device Metadata:</strong> We collect system identifiers (UUIDs), hostnames, and IP addresses to properly route and display your fleet data on your interactive dashboard.</li>
                            </ul>
                            <div className="mt-6 p-4 bg-emerald-50/50 rounded-2xl ring-1 ring-emerald-200/50">
                                <p className="text-xs font-bold text-emerald-700 leading-relaxed">
                                    <span className="uppercase tracking-widest block mb-1">Crucial Note:</span>
                                    We do not inspect the contents of your files, running processes, memory payloads, or internal network packets. Our agents are strictly limited to top-level aggregate hardware telemetry.
                                </p>
                            </div>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-emerald-500 flex items-center justify-center text-xs">03</span>
                                How We Use Your Information
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed mb-4">
                                The collected data is utilized exclusively for the following operational purposes:
                            </p>
                            <ul className="list-none space-y-3 text-sm font-medium text-zinc-600">
                                <li className="flex items-start gap-3"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0" />To provide real-time dashboard visualizations and fleet management capabilities to your registered organization.</li>
                                <li className="flex items-start gap-3"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0" />To trigger threshold-based alerts (e.g., when CPU exceeds 90%).</li>
                                <li className="flex items-start gap-3"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0" />To maintain, secure, and improve the underlying infrastructure of the Service.</li>
                                <li className="flex items-start gap-3"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0" />To enforce our Terms of Service and subscription tier limits.</li>
                            </ul>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-emerald-500 flex items-center justify-center text-xs">04</span>
                                Data Security and Confidentiality
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                We implement industry-standard security measures, including HTTPS encryption for data in transit and cryptographic hashing for stored credentials. Telemetry data is isolated per organization using secure multi-tenant partitioning in our PostgreSQL databases. However, no absolute guarantee can be made regarding the security of Internet transmissions; users acknowledge this inherent risk.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-emerald-500 flex items-center justify-center text-xs">05</span>
                                Data Retention and Deletion
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                Telemetry metrics are retained based on the data retention policy corresponding to your subscription tier. Once data exceeds the retention window or your account is terminated, it is permanently expunged from our operational databases. Backups may retain encrypted fragments of data for up to 30 days post-deletion. Once deleted, historical data cannot be recovered.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-emerald-500 flex items-center justify-center text-xs">06</span>
                                Third-Party Disclosures
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                We do not sell, trade, or otherwise transfer your personally identifiable information or system telemetry data to outside parties. This does not include trusted third parties who assist us in operating our website, conducting our business, or servicing you, so long as those parties agree to keep this information confidential and comply with strict data processing agreements.
                            </p>
                        </section>

                        <div className="mt-12 pt-8 border-t border-zinc-100 flex flex-wrap gap-4 items-center justify-center">
                            <Link href="/terms-of-service" className="text-xs font-black uppercase tracking-widest text-zinc-400 hover:text-zinc-800 transition-colors px-6 py-3 bg-zinc-50 rounded-full ring-1 ring-zinc-200">
                                Terms of Service &rarr;
                            </Link>
                            <Link href="/cookie-policy" className="text-xs font-black uppercase tracking-widest text-zinc-400 hover:text-zinc-800 transition-colors px-6 py-3 bg-zinc-50 rounded-full ring-1 ring-zinc-200">
                                Cookie Policy &rarr;
                            </Link>
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    )
}
