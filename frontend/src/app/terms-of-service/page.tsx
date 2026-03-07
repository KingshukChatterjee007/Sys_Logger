'use client'

import React from 'react'
import { ArrowLeft, FileText } from 'lucide-react'
import Link from 'next/link'
import { motion } from 'framer-motion'

export default function TermsOfServicePage() {
    return (
        <div className="min-h-screen bg-[#FAFAFA] text-zinc-900 font-sans p-6 lg:p-12 selection:bg-zinc-500/30">
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
                    <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] bg-zinc-400/10 rounded-full blur-[100px] pointer-events-none" />

                    <div className="flex flex-col md:flex-row md:items-center gap-6 mb-12 relative z-10 border-b border-zinc-100 pb-10">
                        <div className="w-20 h-20 bg-gradient-to-br from-zinc-800 to-zinc-900 text-white rounded-3xl flex items-center justify-center shadow-xl shadow-zinc-900/10 shrink-0">
                            <FileText className="w-10 h-10" />
                        </div>
                        <div>
                            <h1 className="text-4xl lg:text-5xl font-black uppercase tracking-tight text-zinc-900 mb-3">Terms of Service</h1>
                            <p className="text-xs font-black tracking-widest text-zinc-400 uppercase">Effective Date: October 2026</p>
                        </div>
                    </div>

                    <div className="space-y-6 relative z-10">
                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-zinc-500 flex items-center justify-center text-xs">01</span>
                                Acceptance of Terms
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                By accessing, registering for, and using System Logger PRO ("the Service", "SysLg", "System Logger"), you accept and agree to be bound by the terms and provisions of this agreement ("Terms of Service"). Any participation in this Service will constitute acceptance of this agreement. If you do not agree to abide by the above, please do not use this Service.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-zinc-500 flex items-center justify-center text-xs">02</span>
                                Description of Service
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                System Logger PRO is a real-time system monitoring, telemetry, and fleet management platform. The Service allows organizations to deploy client agents to monitor hardware metrics such as CPU usage, RAM allocation, GPU compute load, and Network Traffic. The Service is provided subject to the subscription tiers and usage limitations detailed on our pricing page.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-zinc-500 flex items-center justify-center text-xs">03</span>
                                User Responsibilities & Account Security
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                Organization Account Details ("Admin Accounts") are strictly responsible for maintaining the confidentiality of their login credentials and authorization keys. Organizations are legally accountable for all actions performed by agents deployed under their authorization. You agree to notify us immediately of any unauthorized use of your account or any other breach of security.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-zinc-500 flex items-center justify-center text-xs">04</span>
                                Subscription Tiers and Fair Usage
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                Accounts are classified into specific tiers (e.g., "Individual" and "Business"). The "Individual" tier is restricted to a maximum of one (1) monitored node. The "Business" tier allows for an unrestricted number of nodes but is subject to fair usage policies regarding API polling frequency and historical data ingestion. Evading connection limits by artificially rotating authorization keys or spoofing system identifiers will result in immediate termination of service without prior notice.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-zinc-500 flex items-center justify-center text-xs">05</span>
                                Intellectual Property
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                The Service and its original content, features, functionalities, and agent source code are and will remain the exclusive property of System Logger PRO and its licensors. The Service is protected by copyright, trademark, and other intellectual property laws. You may not modify, reproduce, distribute, create derivative works or adaptations of, publicly display or in any way exploit any of the content, software, or materials available on the Service, in whole or in part, except as expressly authorized by us.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-zinc-500 flex items-center justify-center text-xs">06</span>
                                Disclaimer of Warranties
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                The Service is provided on an "AS IS" and "AS AVAILABLE" basis. We disclaim all warranties of any kind, whether express or implied, including but not limited to the implied warranties of merchantability, fitness for a particular purpose, and non-infringement. We make no warranty that the Service will meet your specific requirements, will be uninterrupted, timely, secure, or error-free.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-zinc-500 flex items-center justify-center text-xs">07</span>
                                Limitation of Liability
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                In no event shall System Logger PRO, nor its directors, employees, partners, agents, suppliers, or affiliates, be liable for any indirect, incidental, special, consequential or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from (i) your access to or use of or inability to access or use the Service; (ii) any conduct or content of any third party on the Service; (iii) any content obtained from the Service; and (iv) unauthorized access, use or alteration of your transmissions or content.
                            </p>
                        </section>

                        <section className="bg-zinc-50/50 rounded-3xl p-6 lg:p-8 ring-1 ring-zinc-100/50 hover:bg-zinc-50 transition-colors">
                            <h3 className="text-sm font-black uppercase tracking-widest text-zinc-800 mb-4 flex items-center gap-3">
                                <span className="w-8 h-8 rounded-xl bg-white shadow-sm ring-1 ring-zinc-200 text-zinc-500 flex items-center justify-center text-xs">08</span>
                                Modifications to Service
                            </h3>
                            <p className="text-sm font-medium text-zinc-600 leading-relaxed">
                                We reserve the right at any time and from time to time to modify or discontinue, temporarily or permanently, the Service (or any part thereof) with or without notice. We shall not be liable to you or to any third party for any modification, price change, suspension, or discontinuance of the Service.
                            </p>
                        </section>

                        <div className="mt-12 pt-8 border-t border-zinc-100 flex flex-wrap gap-4 items-center justify-center">
                            <Link href="/privacy-policy" className="text-xs font-black uppercase tracking-widest text-zinc-400 hover:text-zinc-800 transition-colors px-6 py-3 bg-zinc-50 rounded-full ring-1 ring-zinc-200">
                                Privacy Policy &rarr;
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
