import { Button } from "@/components/ui/button";
import Link from "next/link";
import { FaGithub } from "react-icons/fa";
import { Badge } from "@/components/ui/badge";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 p-8">
      <div className="text-center max-w-2xl">
        <h1 className="text-5xl font-bold text-gray-800 dark:text-white mb-6">
          LangChain, Next.js & FastAPI
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
          Código pronto para acelerar o desenvolvimento de aplicações AI modernas.
        </p>

        {/* Link to Projects */}
        <Link href="/projects">
          <Button className="px-8 py-4 text-xl font-semibold rounded-full shadow-lg bg-gradient-to-r from-green-700 to-emerald-600 text-white hover:from-green-600 hover:to-emerald-600 focus:ring-4 focus:ring-blue-300">
            Acessar Meus Projetos
          </Button>
        </Link>

        
      </div>
    </main>
  );
}
