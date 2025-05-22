import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "../api/auth/[...nextauth]/route";
import Chatbot from "../../components/ChatClient";

export const dynamic = "force-dynamic";

export default async function ChatPage() {
    const session = await getServerSession(authOptions);

    if (!session) {
        redirect(`/api/auth/signin?callbackUrl=${encodeURIComponent("/chat")}`);
    }

    const userEmail = session.user?.email ?? "";
    
    return <Chatbot email={userEmail}/>;
}
