import { motion, AnimatePresence } from 'motion/react'
import { X } from 'lucide-react'
import { useEffect } from 'react'

export function ImageModal({ isOpen, onClose, imageSrc, fileName }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm"
          />

          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ type: 'spring', damping: 25 }}
              className="relative max-h-[90vh] max-w-[90vw]"
            >
              <button
                type="button"
                onClick={onClose}
                className="absolute -right-4 -top-4 z-10 rounded-full bg-slate-800 p-2 text-slate-300 transition-colors hover:bg-slate-700 hover:text-white"
                aria-label="Close enlarged image"
              >
                <X className="h-5 w-5" />
              </button>

              <img
                src={imageSrc}
                alt={fileName || 'Enlarged view'}
                className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain"
              />

              {fileName ? (
                <div className="mt-4 text-center text-sm text-slate-400">{fileName}</div>
              ) : null}
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
