import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Chat = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();

  // If not authenticated on client side, navigate to login
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, isLoading, navigate]);

  // If loading or not authenticated, show nothing
  if (isLoading || !isAuthenticated) {
    return null;
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">Protected Chat Page</h1>
        <p className="text-gray-600">You are successfully authenticated and in the chat area!</p>
      </div>
    </div>
  );
};

export default Chat; 