import { Button } from "@/components/ui/button";
import Link from "next/link";


export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 p-8">
      <div className="text-center max-w-2xl">
        <h1 className="text-5xl font-bold text-[#0F4098] dark:text-white mb-6">
          Labin Studio
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
          Protótipo de chat conversacional com documentos PDF, desenvolvido pelo Labin
        </p>

        {/* Link to Projects */}
        <Link href="/projects">
          <Button className="px-8 py-4 text-xl font-semibold rounded-lg shadow-lg bg-black text-white hover:bg-gray-800 focus:ring-4 focus:ring-blue-300">
            Meus Projetos
          </Button>
        </Link>

        
      </div>
    </main>
  );
}
