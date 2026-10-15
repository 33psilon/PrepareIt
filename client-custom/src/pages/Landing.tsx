import React, { useState, useEffect } from 'react';
import { ArrowUpRight, Search, Brain, Star, BarChart, CheckCircle, Menu, X, Sun, Moon } from 'lucide-react';
import { SignInButton, useAuth } from "@clerk/clerk-react";
import { useNavigate } from 'react-router-dom';


const LandingPage = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState('ai');
  const [fade, setFade] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const { isSignedIn, isLoaded } = useAuth();
  const navigate = useNavigate();

  // Handle navigation after successful authentication
  React.useEffect(() => {
    if (isLoaded && isSignedIn) {
      navigate('/interviews');
    }
  }, [isLoaded, isSignedIn, navigate]);

  // Load dark mode preference from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
    }
  }, []);

  // Apply dark mode class to document
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleFeatureClick = (key: React.SetStateAction<string>) => {
    if (key !== selectedFeature) {
      setFade(true);
      setTimeout(() => {
        setSelectedFeature(key);
        setFade(false);
      }, 200); // Duration matches fade-out
    }
  };


  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };


  return (
    <div className={`min-h-screen font-sans antialiased relative shadow-[0_35px_60px_-15px_rgba(0,0,0,0.5)] transition-colors duration-300 ${isDarkMode ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-900'}`}>
      {/* Rotating Circle Overlay - separate from the grid */}
      <div
        className="absolute z-30"
        style={{
          top: '370px',         
          left: '412px',        // star adjustment
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
        }}
      >
        <div style={{ position: 'relative', width: 220, height: 220 }}>
          {/* Rotating Circle */}
          <svg
            width="220"
            height="220"
            viewBox="0 0 128 128"
            className="animate-spin-slow"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              mixBlendMode: isDarkMode ? 'normal' : 'difference', // Apply blend mode to the SVG itself
            }}
          >
            <path
              id="curve"
              fill="transparent"
              d="M 64,64 m -48,0 a 48,48 0 1,1 96,0 a 48,48 0 1,1 -96,0"
            />
            <text
              className="text-xs"
              style={{ fill: isDarkMode ? 'white' : 'black', fontSize: '8px', transition: 'fill 0.3s ease' }}
            >
              <textPath href="#curve">
                REAL-TIME FEEDBACK ‎ ‎ • AI-POWERED INTERVIEWS •‎ DSA MASTERY • LIVE SUPPORT •
              </textPath>
            </text>
          </svg>
          {/* Centered Star SVG, larger, black/white depending on theme, counter-clockwise spin */}
          <div

            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="40" height="40" viewBox="0 0 24 24" fill={isDarkMode ? "white" : "black"} xmlns="http://www.w3.org/2000/svg" style={{ transition: 'fill 0.3s ease' }}>
              <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
            </svg>
          </div>
        </div>
      </div>
      <div className={`max-w-6xl mx-auto rounded-3xl overflow-hidden my-2 md:my-4 shadow-sm px-4 md:px-8 transition-colors duration-300 ${isDarkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'}`}>
        {/* Header */}
        <header className="py-1 md:py-2 flex justify-between items-center">
          <div className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="120" height="100" viewBox="0 0 184 100" xmlSpace="preserve">
              <path fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round" stroke-width="7" d="M96.5 62.5c5.637 3.522 8.581 3.435 12.991-.51 2.548-2.28 5.218-4.473 7.464-7.03 4.298-4.889 4-10.44-.455-14.46-3.5-3.158-9.35-2.568-13.488 1.512-6.546 6.454-13.031 12.970-19.498 19.501-1.589 1.605-3.203 3.087-5.515 3.482-4.569.78-6.932-1.15-7.999-6.495M90 41c-5.635-3.591-8.483-2.921-13.565 1.424-7.553 6.458-13.248 14.803-21.424 20.59C50.829 65.975 46.43 65.675 43 62c-2.596-2.78-3.064-9.425-.444-12.452 2.923-3.377 5.94-6.854 9.536-9.418 3.793-2.705 8.14-2.25 11.908.87"/>
            </svg>
            
            {/* Desktop Navigation */}
            <nav className="ml-12 hidden md:flex gap-8">
              <a href="#" className={`text-sm hover:text-purple-600 ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Home</a>
              <a href="#" className={`text-sm hover:text-purple-600 ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>About us</a>
              <a href="#" className={`text-sm hover:text-purple-600 ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Practice</a>
              <a href="#" className={`text-sm hover:text-purple-600 ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Blog</a>
              <a href="#" className={`text-sm hover:text-purple-600 ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Contacts</a>
            </nav>
          </div>
          
          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button onClick={toggleMobileMenu} className="focus:outline-none">
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
          
          {/* Desktop Header Right Section */}
          <div className="hidden md:flex items-center gap-4">
            {/* Dark Mode Toggle */}
            <div className="relative">
              <button
                onClick={toggleDarkMode}
                className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'}`}
              >
                <span className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform duration-300 ${isDarkMode ? 'translate-x-7' : 'translate-x-1'}`}>
                  {isDarkMode ? (
                    <Moon className="h-3.5 w-3.5 text-gray-800 m-1.5" />
                  ) : (
                    <Sun className="h-3.5 w-3.5 text-yellow-500 m-1.5" />
                  )}
                </span>
              </button>
            </div>

            <SignInButton>
              <button className={`text-base font-semibold px-6 py-2 rounded-full shadow-lg transition-all duration-300 transform hover:scale-105 focus:scale-100 focus:outline-none animate-pulse-slow ${isDarkMode ? 'bg-purple-600 hover:bg-purple-700 text-white' : 'bg-black hover:bg-gray-900 text-white'}`} style={{ minWidth: 120, letterSpacing: '0.03em' }}>
                Start Practicing
              </button>
            </SignInButton>
          </div>
        </header>
        
        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className={`md:hidden py-4 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
            <nav className="flex flex-col gap-4">
              <a href="#" className={`text-sm ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Home</a>
              <a href="#" className={`text-sm ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>About us</a>
              <a href="#" className={`text-sm ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Practice</a>
              <a href="#" className={`text-sm ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Blog</a>
              <a href="#" className={`text-sm ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Contacts</a>
            </nav>
            <div className="mt-4 flex flex-col gap-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search"
                  className={`pl-9 pr-4 py-2 rounded-full border text-sm w-full focus:outline-none focus:ring-1 ${isDarkMode ? 'border-gray-600 bg-gray-700 text-white focus:ring-purple-500 placeholder-gray-400' : 'border-gray-200 focus:ring-black'}`}
                />
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              </div>
              <SignInButton>
                <button className={`text-sm font-medium px-5 py-2 rounded-full transition w-full hover:shadow-lg ${isDarkMode ? 'bg-purple-600 hover:bg-purple-700 text-white' : 'bg-black hover:bg-gray-900 text-white'}`}>
                  Start Practicing
                </button>
              </SignInButton>
            </div>
          </div>
        )}
        
        {/* Hero Section */}
        <section className="pt-6 md:pt-10 pb-6 grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-8">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-light leading-tight tracking-tight">
              MASTER
              <br />
              <span className="ml-15">DSA INTERVIEWS</span>
              <br />
              <span className="inline-block px-6 py-2 text-base font-medium border border-black rounded-full align-middle text-xl ml-50">WITH</span>
              <br />
              <span className="ml-30">AI MENTORSHIP</span>
            </h1>
            
            
          </div>
          
          <div className="md:col-span-4 bg-black rounded-3xl overflow-hidden text-white relative hover:border hover:border-gray-300 transition-colors duration-200">
            {/* Background GIF */}
            <img
              src="/4b20e05879b68f413efca4c6dd4ae13a.gif"
              alt="AI Interview Simulation"
              className="absolute inset-0 w-full h-full object-cover opacity-60 z-10"
            />
            {/* Overlay for gradient if needed */}
            <div className="absolute inset-0 bg-gradient-to-br from-black via-transparent to-black z-10"></div>
            {/* Card Content */}
            <div className="relative z-20 p-5 h-full flex flex-col justify-between">
              <div className="flex justify-between items-start">
                <span className="text-sm px-2 py-2 border border-white rounded-full">AI-Powered</span>
                <div className="animate-spin-slow-reverse absolute top-4 right-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" fill="white"/>
                  </svg>
                </div>
              </div>
              <div className="mt-12 mb-8">
                <p className="text-sm leading-relaxed text-zinc-100">
                  Practice data structures and algorithms with real-time AI feedback, voice interactions, and personalized interview simulations.
                </p>
              </div>
            </div>
          </div>
        </section>
        
        {/* Stats & Brain Section */}
        <section className="py-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-12 gap-6">
          <div className="md:col-span-6 rounded-3xl overflow-hidden shadow-lg hover:shadow-2xl transition-shadow duration-300 relative">
            <img
              src="/b94a76bce98603c151bf75c79ccd0516.gif"
              alt="DSA problem solving visualization"
              className="w-full h-full object-cover grayscale rounded-3xl"
            />
          </div>
          
          <div className={`md:col-span-3 rounded-3xl p-6 flex flex-col justify-center items-center shadow-lg hover:shadow-2xl transition-shadow duration-300 ${isDarkMode ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-900'}`}>
            <h2 className={`text-5xl font-bold mb-1 ${isDarkMode ? 'text-zinc-200' : 'text-zinc-800'}`}>200+</h2>
            <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>DSA Problems</p>
          </div>
          
          <div className="md:col-span-3 bg-black rounded-3xl p-6 flex flex-col justify-center items-center text-white shadow-lg hover:shadow-2xl transition-shadow duration-300 hover:border hover:border-gray-300 transition-colors duration-200">
            <h2 className="text-5xl font-bold mb-1 text-zinc-100">Live</h2>
            <p className="text-sm text-zinc-100">Feedback</p>
          </div>
        </section>
        
        {/* Features Section */}
        <section className="py-4">
          <div className="bg-[#e6ff82] rounded-3xl p-6 md:p-8 shadow-lg hover:shadow-2xl transition-shadow duration-300 group">
            <div className="flex flex-wrap gap-3 mb-6">
              {featureOptions.map(option => (
                <button
                  key={option.key}
                  onClick={() => handleFeatureClick(option.key)}
                  className={`text-xs px-4 py-1.5 rounded-full font-medium transition-all duration-200
                    ${selectedFeature === option.key
                      ? 'bg-black text-white scale-105 shadow-lg'
                      : 'border border-black text-black bg-transparent hover:bg-black hover:text-white hover:scale-105'}
                  `}
                  style={{ outline: 'none' }}
                >
                  {option.label}
                </button>
              ))}
            </div>
            
            <div className="flex flex-col md:flex-row justify-between items-start gap-4">
              <div className="max-w-xl">
                <h2 className={`text-3xl md:text-4xl font-bold mb-4 ${isDarkMode ? 'text-black' : 'text-gray-900'}`}>Why PrepareIt AI?</h2>
                <p
                  className={`text-base md:text-lg leading-relaxed transition-opacity duration-200 ${isDarkMode ? 'text-black' : 'text-gray-900'} ${fade ? 'opacity-0' : 'opacity-100'}`}
                  key={selectedFeature}
                >
                  {featureOptions.find(opt => opt.key === selectedFeature)?.copy}
                </p>
              </div>
              
              <span className="transition-transform duration-300 ease-in-out -translate-y-1 group-hover:-translate-y-3">
                <ArrowUpRight className="w-16 h-16 stroke-1" />
              </span>
            </div>
          </div>
        </section>
        
        {/* Course Categories */}
        <section className="py-8 md:py-10">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
            <h2 className={`text-2xl md:text-3xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Interview Types You'll Master</h2>
            <button className={`text-sm flex items-center gap-2 hover:underline ${isDarkMode ? 'text-zinc-400 hover:text-zinc-300' : 'text-gray-600 hover:text-gray-800'}`}>
              Explore all types <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { name: "Arrays & Strings", courses: "50+ problems", icon: <Brain className="w-6 h-6" /> },
              { name: "Trees & Graphs", courses: "40+ problems", icon: <BarChart className="w-6 h-6" /> },
              { name: "Dynamic Programming", courses: "30+ problems", icon: <div className="font-mono text-lg">DP</div> },
              { name: "System Design", courses: "25+ scenarios", icon: <Star className="w-6 h-6" /> }
            ].map((category, index) => (
              <div key={index} className={`border rounded-2xl p-6 transition-colors shadow-lg hover:shadow-2xl transition-shadow duration-300 ${isDarkMode ? 'border-gray-600 bg-gray-700 hover:border-purple-400' : 'border-gray-200 bg-white hover:border-black'}`}>
                <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 ${isDarkMode ? 'bg-gray-600' : 'bg-gray-100'}`}>
                  {category.icon}
                </div>
                <h3 className={`text-lg font-medium mb-1 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{category.name}</h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{category.courses}</p>
              </div>
            ))}
          </div>
        </section>
        
        {/* Learning Experience */}
        <section className="py-8 md:py-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            <div className="lg:col-span-5">
              <h2 className={`text-3xl md:text-4xl font-bold mb-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Practice Like Real Interviews</h2>
              <p className={`text-base md:text-lg mb-8 leading-relaxed ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Experience realistic mock interviews with AI-powered feedback, voice interactions, and real-time code evaluation using Monaco Editor.
              </p>
              
              <SignInButton>
                <button className={`text-sm font-medium px-5 py-3 rounded-full transition flex items-center gap-2 ${isDarkMode ? 'bg-purple-600 hover:bg-purple-700 text-white' : 'bg-black hover:bg-gray-900 text-white'}`}>
                  Try Mock Interview <ArrowUpRight className="w-4 h-4" />
                </button>
              </SignInButton>
            </div>
            
            <div className="lg:col-span-7">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {[
                  {
                    title: "Voice-Powered Interviews",
                    description: "Practice explaining your solutions aloud with real-time speech recognition and AI feedback"
                  },
                  {
                    title: "Live Code Editor",
                    description: "Code in a professional IDE environment with syntax highlighting and auto-completion"
                  },
                  {
                    title: "Instant AI Feedback",
                    description: "Get immediate insights on your approach, code quality, and optimization opportunities"
                  },
                  {
                    title: "Personalized Learning",
                    description: "Adaptive problem selection based on your strengths, weaknesses, and interview goals"
                  }
                ].map((feature, index) => (
                  <div key={index} className={`rounded-2xl p-6 shadow-lg hover:shadow-2xl transition-shadow duration-300 ${isDarkMode ? 'bg-gray-600' : 'bg-gray-50'}`}>
                    <div className="w-10 h-10 rounded-full bg-[#e6ff82] flex items-center justify-center mb-4">
                      <CheckCircle className="w-5 h-5" />
                    </div>
                    <h3 className={`text-lg font-medium mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{feature.title}</h3>
                    <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{feature.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
        
        {/* Testimonials */}
        <section className={`py-8 md:py-10 rounded-3xl mx-0 md:mx-8 mb-8 shadow-lg hover:shadow-2xl transition-shadow duration-300 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
          <div className="px-4 md:px-8">
            <div className="flex justify-between items-center mb-8">
              <h2 className={`text-2xl md:text-3xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Success Stories</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  name: "Alex Johnson",
                  role: "Software Engineer at Google",
                  quote: "PrepareIt AI helped me nail my FAANG interviews. The voice practice was a game-changer.",
                  rating: 5
                },
                {
                  name: "Sarah Miller",
                  role: "Backend Developer",
                  quote: "The real-time feedback on my coding approach helped me optimize solutions I never thought possible.",
                  rating: 5
                },
                {
                  name: "David Chen",
                  role: "Full-Stack Engineer",
                  quote: "Finally, a platform that simulates real interview pressure. Got my dream job after 3 weeks of practice.",
                  rating: 4
                }
              ].map((testimonial, index) => (
                <div key={index} className={`rounded-2xl p-6 border shadow-lg hover:shadow-2xl transition-shadow duration-300 ${isDarkMode ? 'bg-gray-600 border-gray-500' : 'bg-white border-gray-100'}`}>
                  <div className="flex gap-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className={`w-4 h-4 ${isDarkMode ? 'text-yellow-400' : ''} ${i < testimonial.rating ? 'fill-yellow-400 text-yellow-400' : (isDarkMode ? 'text-gray-500' : 'text-gray-200')}`} />
                    ))}
                  </div>
                  <p className={`text-sm mb-6 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>"{testimonial.quote}"</p>
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-medium ${isDarkMode ? 'bg-gray-500' : 'bg-gray-200'}`}>
                      {testimonial.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <p className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{testimonial.name}</p>
                      <p className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{testimonial.role}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
        
        {/* CTA Section */}
        <section className="py-8 md:py-10 mb-8">
          <div className="bg-black rounded-3xl p-6 md:p-10 text-white shadow-lg hover:shadow-2xl transition-shadow duration-300">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-3xl md:text-4xl font-bold mb-4 text-zinc-100">Ready to Ace Your Next Interview?</h2>
              <p className="text-base md:text-lg opacity-80 mb-8 text-zinc-100">
                Join thousands of developers who've landed their dream jobs with AI-powered interview preparation.
              </p>
              <SignInButton>
                <button className="bg-white text-black text-sm font-medium px-6 md:px-8 py-3 rounded-full hover:bg-gray-100 transition hover:shadow-lg">
                  Start Your Journey
                </button>
              </SignInButton>
              <p className="text-sm opacity-60 mt-4 text-zinc-200">Begin with a free mock interview. No credit card required.</p>
            </div>
          </div>
        </section>
        
        {/* Footer */}
        <footer className={`py-6 border-t ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-100 bg-white'}`}>
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="120" height="100" viewBox="0 0 184 100" xmlSpace="preserve">
                <path fill="none" stroke={`${isDarkMode ? '#fff' : '#000'}`} strokeLinecap="round" strokeLinejoin="round" strokeWidth="7" d="M96.5 62.5c5.637 3.522 8.581 3.435 12.991-.51 2.548-2.28 5.218-4.473 7.464-7.03 4.298-4.889 4-10.44-.455-14.46-3.5-3.158-9.35-2.568-13.488 1.512-6.546 6.454-13.031 12.970-19.498 19.501-1.589 1.605-3.203 3.087-5.515 3.482-4.569.78-6.932-1.15-7.999-6.495M90 41c-5.635-3.591-8.483-2.921-13.565 1.424-7.553 6.458-13.248 14.803-21.424 20.59C50.829 65.975 46.43 65.675 43 62c-2.596-2.78-3.064-9.425-.444-12.452 2.923-3.377 5.94-6.854 9.536-9.418 3.793-2.705 8.14-2.25 11.908.87"/>
              </svg>
              <span className={`ml-3 text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>© 2025 PrepareIt AI. All rights reserved.</span>
            </div>

            <div className="flex gap-6">
              <a href="#" className={`text-sm hover:text-purple-600 ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Privacy Policy</a>
              <a href="#" className={`text-sm hover:text-purple-600 ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Terms of Service</a>
              <a href="#" className={`text-sm hover:text-purple-600 ${isDarkMode ? 'text-gray-300 hover:text-purple-400' : 'text-gray-600 hover:text-black'}`}>Contact Us</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};


export default LandingPage;


const featureOptions = [
  {
    key: 'ai',
    label: 'AI-powered interviews',
    copy: "Experience the future of interview preparation with our AI-powered mock interviews. Get real-time feedback on your coding approach, communication skills, and problem-solving techniques through voice interactions and live code analysis.",
  },
  {
    key: 'career',
    label: 'Career advancement',
    copy: "Boost your career prospects with targeted DSA practice designed for today's top tech companies. Our platform adapts to your skill level and focuses on the exact interview patterns used by FAANG and unicorn startups.",
  },
  {
    key: 'community',
    label: 'Real-time feedback',
    copy: "Get instant, actionable feedback on your solutions with our advanced AI system. From code optimization suggestions to communication improvements, every practice session helps you grow closer to interview success.",
  },
];
