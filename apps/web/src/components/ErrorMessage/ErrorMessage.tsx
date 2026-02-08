import './ErrorMessage.css'

interface ErrorMessageProps {
  message: string
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <div className="error-message" role="alert">
      <strong>Error:</strong> {message}
    </div>
  )
}
