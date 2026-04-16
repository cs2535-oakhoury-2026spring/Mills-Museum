import { motion, AnimatePresence } from 'motion/react'
import { X } from 'lucide-react'
import { useEffect } from 'react'

/**
 * Full-screen image modal (controlled).
 *
 * `isOpen` and `onClose` are owned by the parent so the modal has no hidden state.
 * This component focuses on UX details: escape-to-close, click-backdrop-to-close,
 * scroll locking, and mount/unmount animations.
 */
export function ImageModal({ isOpen, onClose, imageSrc, fileName }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      // Keep keyboard close behavior local to the modal and clean it up reliably.
      document.addEventListener('keydown', handleEscape)
      // Prevent background scroll while the overlay is open.
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
            // Backdrop sits behind the dialog content and closes on click.
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
                className="absolute -right-4 -top-4 z-10 rounded-full border-2 border-white/80 bg-mcam-navy p-2 text-white shadow-lg transition-colors hover:brightness-110"
                aria-label="Close enlarged image"
              >
                <X className="h-5 w-5" />
              </button>

              <img
                src={imageSrc}
                alt={fileName || 'Enlarged view'}
                // Constrain to viewport while preserving aspect ratio.
                className="box-border mx-auto block h-auto max-h-[90vh] w-auto max-w-[90vw] rounded-lg object-contain object-center"
              />

              {fileName ? (
                <div className="mt-4 text-center text-sm text-white/90">{fileName}</div>
              ) : null}
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
