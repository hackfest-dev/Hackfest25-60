import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ChatLayout from '../../components/chat/ChatLayout';

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

  return <ChatLayout />;
};

export default Chat; 