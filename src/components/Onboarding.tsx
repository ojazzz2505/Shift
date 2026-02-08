import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Monitor, ArrowRight, Sparkles, FolderArchive, ScrollText, HardDrive, Download, Folder, SlidersHorizontal } from 'lucide-react'
import { useAppStore } from '../store/appStore'

interface OnboardingProps {
    onComplete: () => void
}

type StepConfig = {
    title: string
    desc: string
    icon: any
    targetId?: string
    placement?: 'left' | 'right' | 'top' | 'bottom' | 'center'
    inflation?: number
}

export default function Onboarding({ onComplete }: OnboardingProps) {
    // Tour state - simplified, no more dependency checking (handled by FirstRunModal)
    // Tour state
    const [currentStepIndex, setCurrentStepIndex] = useState(0)
    const [highlightRect, setHighlightRect] = useState<DOMRect | null>(null)
    const resizeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const measureRetryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    const { setSettingsOpen } = useAppStore()

    const tourSteps: StepConfig[] = [
        // Settings sections - Top to Bottom order (visible when drawer opens)
        {
            title: "Auto-Save Preferences",
            desc: "Automatically save your conversion history and logs.",
            icon: Sparkles,
            targetId: "tour-autosave-settings",
            placement: "left",
            inflation: 0
        },
        {
            title: "Output Paths",
            desc: "Organize your converted files into custom folders.",
            icon: Folder,
            targetId: "tour-output-paths",
            placement: "left",
            inflation: 0
        },
        {
            title: "UI Scale",
            desc: "Adjust the interface size to your preference.",
            icon: SlidersHorizontal,
            targetId: "tour-ui-scale",
            placement: "left",
            inflation: 0
        },
        {
            title: "Hardware Acceleration",
            desc: "Select your preferred GPU to speed up conversions.",
            icon: Monitor,
            targetId: "tour-gpu-settings",
            placement: "left",
            inflation: 0
        },
        {
            title: "Installed Dependencies",
            desc: "Check the status of tools like FFmpeg and ImageMagick.",
            icon: HardDrive,
            targetId: "tour-dependencies",
            placement: "left",
            inflation: 0
        },
        {
            title: "Dependency Manager",
            desc: "Repair or reinstall missing dependencies easily.",
            icon: Download,
            targetId: "tour-dependency-manager",
            placement: "left",
            inflation: 0
        },
        // Header items
        {
            title: "Archive",
            desc: "Browse your history of converted files.",
            icon: FolderArchive,
            targetId: "tour-archive-button",
            placement: "bottom",
            inflation: 6
        },
        {
            title: "Activity Logs",
            desc: "Track detailed logs of your conversion tasks.",
            icon: ScrollText,
            targetId: "tour-logs-button",
            placement: "bottom",
            inflation: 6
        },
        {
            title: "Ready to Start!",
            desc: "Drag and drop files to start converting immediately.",
            icon: Sparkles,
            targetId: "tour-dropzone",
            placement: "bottom",
            inflation: 0
        }
    ]

    // Open settings drawer on mount for the first step
    useEffect(() => {
        setSettingsOpen(true)
    }, [])

    // Step Change Effect
    useEffect(() => {
        const currentStep = tourSteps[currentStepIndex]

        // IDs that require settings drawer to be open
        const settingsDrawerIds = [
            'tour-dependency-manager',
            'tour-dependencies',
            'tour-gpu-settings',
            'tour-ui-scale',
            'tour-output-paths',
            'tour-autosave-settings'
        ]
        const isInSettings = currentStep.targetId && settingsDrawerIds.includes(currentStep.targetId)

        // Handle Drawer
        // We set this immediately. If the previous step was in the drawer and this one isn't,
        // the drawer will start closing animation via its own component.
        // Since the drawer is an overlay (fixed position), it doesn't affect the Header layout.
        if (isInSettings) {
            setSettingsOpen(true)
        } else {
            setSettingsOpen(false)
        }

        // Measure function
        const measure = () => {
            if (currentStep.targetId) {
                const el = document.getElementById(currentStep.targetId)
                if (el) {
                    el.scrollIntoView({ behavior: 'auto', block: 'center' })

                    // Standard double RAF ensures layout is settled for the current frame
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            const rect = el.getBoundingClientRect()
                            const inf = currentStep.inflation || 0
                            setHighlightRect(new DOMRect(
                                rect.x - inf,
                                rect.y - inf,
                                rect.width + (inf * 2),
                                rect.height + (inf * 2)
                            ))
                        })
                    })
                } else {
                    measureRetryRef.current = setTimeout(measure, 50)
                }
            }
        }

        // Only delay if we are opening the drawer to allow it to render content
        // Otherwise (closing drawer or navigating within same context), measure immediately.
        const delay = isInSettings ? 600 : 0

        const timer = setTimeout(measure, delay)

        return () => {
            clearTimeout(timer)
            if (measureRetryRef.current) clearTimeout(measureRetryRef.current)
        }
    }, [currentStepIndex])

    // Resize Handler
    useEffect(() => {
        const handleResize = () => {
            if (resizeTimeoutRef.current) clearTimeout(resizeTimeoutRef.current)
            resizeTimeoutRef.current = setTimeout(() => {
                const currentStep = tourSteps[currentStepIndex]
                if (currentStep.targetId) {
                    const el = document.getElementById(currentStep.targetId)
                    if (el) {
                        const rect = el.getBoundingClientRect()
                        const inf = currentStep.inflation || 0
                        setHighlightRect(new DOMRect(
                            rect.x - inf, rect.y - inf,
                            rect.width + (inf * 2), rect.height + (inf * 2)
                        ))
                    }
                }
            }, 100)
        }

        window.addEventListener('resize', handleResize)
        return () => {
            window.removeEventListener('resize', handleResize)
            if (resizeTimeoutRef.current) clearTimeout(resizeTimeoutRef.current)
        }
    }, [currentStepIndex])

    const handleNext = () => {
        if (currentStepIndex < tourSteps.length - 1) {
            const nextIndex = currentStepIndex + 1
            const nextStep = tourSteps[nextIndex]

            if (nextStep.targetId) {
                const el = document.getElementById(nextStep.targetId)
                if (el) {
                    // 1. Scroll FIRST (instantly) if needed
                    // This prevents the "jump" where the box goes to the old position,
                    // then the page scrolls, then the box corrects itself.
                    el.scrollIntoView({ behavior: 'instant', block: 'center' })

                    // 2. Measure immediately after scrolling
                    const rect = el.getBoundingClientRect()
                    const inf = nextStep.inflation || 0
                    setHighlightRect(new DOMRect(
                        rect.x - inf,
                        rect.y - inf,
                        rect.width + (inf * 2),
                        rect.height + (inf * 2)
                    ))
                }
            }

            setCurrentStepIndex(prev => prev + 1)
        } else {
            onComplete()
        }
    }

    const getCardPosition = () => {
        if (!highlightRect) return { top: '50%', left: '50%', x: '-50%', y: '-50%' }
        const stepConfig = tourSteps[currentStepIndex]
        const gap = 20
        let pos = { top: 0, left: 0, x: '0%', y: '0%' }
        switch (stepConfig.placement) {
            case 'left':
                pos = { top: highlightRect.top + (highlightRect.height / 2), left: highlightRect.left - gap, x: '-100%', y: '-50%' }
                break
            case 'right':
                pos = { top: highlightRect.top + (highlightRect.height / 2), left: highlightRect.right + gap, x: '0%', y: '-50%' }
                break
            case 'bottom':
                pos = { top: highlightRect.bottom + gap, left: highlightRect.left + (highlightRect.width / 2), x: '-50%', y: '0%' }
                break
            case 'top':
                pos = { top: highlightRect.top - gap, left: highlightRect.left + (highlightRect.width / 2), x: '-50%', y: '-100%' }
                break
            default:
                pos = { top: highlightRect.top + (highlightRect.height / 2), left: highlightRect.left + (highlightRect.width / 2), x: '-50%', y: '-50%' }
        }

        const W = 320, H = 250, M = 20
        if (pos.y === '-50%') pos.top = Math.max(H / 2 + M, Math.min(pos.top, window.innerHeight - H / 2 - M))
        else if (pos.y === '0%') pos.top = Math.max(M, Math.min(pos.top, window.innerHeight - H - M))
        else if (pos.y === '-100%') pos.top = Math.max(H + M, Math.min(pos.top, window.innerHeight - M))

        if (pos.x === '-50%') pos.left = Math.max(W / 2 + M, Math.min(pos.left, window.innerWidth - W / 2 - M))
        else if (pos.x === '0%') pos.left = Math.max(M, Math.min(pos.left, window.innerWidth - W - M))
        else if (pos.x === '-100%') pos.left = Math.max(W + M, Math.min(pos.left, window.innerWidth - M))

        return pos
    }

    const cardPos = getCardPosition()
    const snappySpring = { type: "spring" as const, stiffness: 400, damping: 35 }
    const isFirstStep = currentStepIndex === 0

    return (
        <div className="fixed inset-0 z-[5000] pointer-events-none">
            {/* Blocker/Dimming Overlay - 4 parts to allow click-through in center */}
            {highlightRect ? (
                <>
                    {/* Top */}
                    <motion.div
                        className="absolute bg-black/50 pointer-events-auto"
                        animate={{ top: 0, left: 0, right: 0, height: highlightRect.top }}
                        transition={snappySpring}
                    />
                    {/* Bottom */}
                    <motion.div
                        className="absolute bg-black/50 pointer-events-auto"
                        animate={{ top: highlightRect.bottom, left: 0, right: 0, bottom: 0 }}
                        transition={snappySpring}
                    />
                    {/* Left */}
                    <motion.div
                        className="absolute bg-black/50 pointer-events-auto"
                        animate={{ top: highlightRect.top, left: 0, width: highlightRect.left, height: highlightRect.height }}
                        transition={snappySpring}
                    />
                    {/* Right */}
                    <motion.div
                        className="absolute bg-black/50 pointer-events-auto"
                        animate={{ top: highlightRect.top, left: highlightRect.right, right: 0, height: highlightRect.height }}
                        transition={snappySpring}
                    />
                </>
            ) : (
                // Fallback full cover if no rect yet
                <div className="absolute inset-0 bg-black/50 pointer-events-auto" />
            )}

            {/* Spotlight Highlight Box (Border Only) */}
            {highlightRect && (
                <motion.div
                    layoutId="highlight-box"
                    initial={isFirstStep ? { opacity: 0 } : false}
                    animate={{
                        opacity: 1,
                        top: highlightRect.top,
                        left: highlightRect.left,
                        width: highlightRect.width,
                        height: highlightRect.height
                    }}
                    transition={{
                        ...snappySpring,
                        opacity: { duration: isFirstStep ? 0.7 : 0.15 }
                    }}
                    // Removed boxShadow - using blockers instead
                    className="absolute border-2 border-blue-500 rounded-lg bg-transparent pointer-events-none z-10"
                />
            )}

            {/* Dialog Card */}
            {highlightRect && (
                <motion.div
                    initial={isFirstStep ? { opacity: 0, scale: 0.95 } : { opacity: 1, scale: 1 }}
                    animate={{
                        opacity: 1,
                        scale: 1,
                        top: cardPos.top,
                        left: cardPos.left,
                        x: cardPos.x,
                        y: cardPos.y
                    }}
                    transition={{
                        ...snappySpring,
                        opacity: { duration: isFirstStep ? 0.7 : 0.2 }
                    }}
                    style={{ position: 'absolute', zIndex: 50 }}
                    className="pointer-events-auto"
                >
                    <div className="bg-[#0a0a0a] border border-neutral-800 p-5 rounded-xl shadow-2xl w-72 relative overflow-hidden">
                        <div className="absolute -top-10 -right-10 w-24 h-24 bg-blue-500/10 rounded-full" style={{ filter: 'blur(30px)' }} />

                        <div className="relative z-10 flex flex-col gap-3">
                            <div className="w-9 h-9 rounded-lg bg-blue-500/15 flex items-center justify-center text-blue-400">
                                {(() => {
                                    const Icon = tourSteps[currentStepIndex].icon
                                    return <Icon className="w-4 h-4" />
                                })()}
                            </div>

                            <div className="min-h-[80px]">
                                <AnimatePresence mode="wait">
                                    <motion.div
                                        key={currentStepIndex}
                                        initial={{ opacity: 0, x: 5 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -5 }}
                                        transition={{ duration: 0.15 }}
                                    >
                                        <h3 className="text-sm font-semibold text-white mb-1">
                                            {tourSteps[currentStepIndex].title}
                                        </h3>
                                        <p className="text-xs text-neutral-400 leading-relaxed">
                                            {tourSteps[currentStepIndex].desc}
                                        </p>
                                    </motion.div>
                                </AnimatePresence>
                            </div>

                            <div className="flex items-center justify-between mt-1">
                                <span className="text-[10px] text-neutral-600">
                                    {currentStepIndex + 1} of {tourSteps.length}
                                </span>
                                <button
                                    onClick={handleNext}
                                    className="bg-white text-black hover:bg-neutral-200 px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors"
                                >
                                    {currentStepIndex === tourSteps.length - 1 ? "Get Started" : "Next"}
                                    <ArrowRight className="w-3 h-3" />
                                </button>
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}
        </div>
    )
}

/*
 * PRESERVED FOR FUTURE USE: App Update Loading Screen
 * 
 * {isUpdating && (
 *     <motion.div className="fixed inset-0 z-[9998] bg-black flex flex-col items-center justify-center">
 *         <div className="w-48 space-y-4 text-center">
 *             <div className="w-6 h-6 mx-auto border-2 border-neutral-700 border-t-white rounded-full animate-spin" />
 *             <p className="text-[10px] text-neutral-500 uppercase tracking-widest font-medium">Updating</p>
 *             <div className="h-0.5 bg-neutral-800 rounded-full overflow-hidden">
 *                 <motion.div className="h-full bg-white" animate={{ width: `${progress}%` }} />
 *             </div>
 *         </div>
 *     </motion.div>
 * )}
 */
