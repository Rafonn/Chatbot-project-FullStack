"use client"

import { motion } from 'framer-motion';
import Link from 'next/link';
import Circle from '../components/ui/Circle';

export default function Home() {
  return (
    <main
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0',
      }}
    >
      <div className='relative top-120'>
        <Circle />
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{
          opacity: 1,
          transition: { delay: 2, duration: 0.4, ease: "easeIn" },
        }}
        className="min-h-screen min-w-screen flex items-center justify-center w-full h-full">
        <div className="w-full max-w-md p-8 rounded overflow-auto">

          <div className="flex justify-center items-center w-full circle-container mt-15 mb-10">
            <div className="circle"></div>
            <div className="circle"></div>
            <div className="circle"></div>
            <div className="circle"></div>
            <div className="circle"></div>
          </div>

          <div className="text-center mb-8" >
            <h1 className="text-white text-5xl font-bold mb-4">
              Andritz PFR AI
            </h1>
            <p className="text-white text-lg">
              Para começar, clique no botão abaixo:
            </p>
          </div>

          <div className='mt-5'>
            <Link href="/login" className='mt-10'>
              <div className="flex items-center justify-center">
                <div className="relative group">
                  <button
                    className="relative inline-block p-px font-semibold leading-6 text-white bg-gray-800 shadow-2xl cursor-pointer rounded-xl shadow-zinc-900 transition-transform duration-300 ease-in-out hover:scale-105 active:scale-95"
                  >
                    <span
                      className="absolute inset-0 rounded-xl bg-gradient-to-r from-teal-400 via-blue-500 to-purple-500 p-[2px] opacity-0 transition-opacity duration-500 group-hover:opacity-100"
                    ></span>

                    <span className="relative z-10 block px-6 py-3 rounded-xl bg-gray-950">
                      <div className="relative z-10 flex items-center space-x-2">
                        <span className="transition-all duration-500 group-hover:translate-x-1"
                        >Let&apos;s get started</span
                        >
                        <svg
                          className="w-6 h-6 transition-transform duration-500 group-hover:translate-x-1"
                          data-slot="icon"
                          aria-hidden="true"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <path
                            clipRule="evenodd"
                            d="M8.22 5.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 0 1 0-1.06Z"
                            fillRule="evenodd"
                          ></path>
                        </svg>
                      </div>
                    </span>
                  </button>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </motion.div>
    </main >
  );
}
