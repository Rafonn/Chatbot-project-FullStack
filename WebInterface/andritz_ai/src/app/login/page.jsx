'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signIn } from 'next-auth/react';
import { motion } from 'framer-motion';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const router = useRouter();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        const result = await signIn('credentials', {
            redirect: false,
            email,
            password,
        });

        const hasError =
            result.error && result.error !== 'undefined';

        if (hasError) {
            setError('Email ou senha inválidos');
        } else {
            router.push('/chat');
        }
    };



    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{
                opacity: 1,
                transition: { delay: 2, duration: 0.4, ease: "easeIn" },
            }}
            className="min-h-screen min-w-screen flex items-center justify-center w-full h-full">
            <div className="w-full max-w-md p-8 rounded shadow rounded-[10%] overflow-auto pulse-shadow">

                <div className="flex justify-center items-center w-full circle-container mt-15">
                    <div className="circle"></div>
                    <div className="circle"></div>
                    <div className="circle"></div>
                    <div className="circle"></div>
                    <div className="circle"></div>
                </div>

                <h1 className="text-2xl font-bold mb-6 text-center text-white">Login</h1>

                {error && (
                    <div className="mb-4 text-red-600 text-sm text-center">
                        {error}
                    </div>
                )}
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label htmlFor="email" className="block text-white mb-2">
                            Email
                        </label>
                        <input
                            type="email"
                            id="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className={`
                            w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-center
                                ${email
                                    ? 'bg-white text-[#006db0]'
                                    : 'text-white'
                                }
                            `}
                        />
                    </div>
                    <div className="mb-6">
                        <label htmlFor="password" className="block text-white mb-2">
                            Senha
                        </label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-white text-center mb-10"
                        />
                    </div>
                    <button className="btn-login" type="submit">Entrar</button>
                </form>
            </div>
        </motion.div>
    );
}
