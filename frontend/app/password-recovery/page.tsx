"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Page() {
  return (
    <div className="flex h-full w-full items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Card className="w-full max-w-sm rounded-lg shadow-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800">
        <CardHeader>
          <CardTitle className="text-xl font-semibold text-gray-800 dark:text-white">
            Recuperar Senha
          </CardTitle>
          <CardDescription className="text-sm text-gray-600 dark:text-gray-400">
            Funcionalidade em desenvolvimento
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6 text-center">
          
          <p className="text-gray-700 dark:text-gray-300">
            Para recuperar a senha, entre em contato com{" "}
            <span className="font-semibold">Luiz Simões</span>.
          </p>

          <div className="pt-4 text-sm">
            <Link
              href="/login"
              className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-500"
            >
              Voltar ao login
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
