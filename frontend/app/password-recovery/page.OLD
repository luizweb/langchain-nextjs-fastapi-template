"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

export default function Page() {
  // Estados do formulário
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Placeholder: Função para enviar email de recuperação
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Implementar chamada à API para enviar email de recuperação
      // await fetch("http://localhost:8000/auth/password-reset", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify({ email }),
      // });
      
      console.log("Email de recuperação enviado para:", email);
      setSuccess(true);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar email");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm">
        <Card className="w-full rounded-lg shadow-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xl font-semibold text-gray-800 dark:text-white">
              Recuperar Senha
            </CardTitle>
            <CardDescription className="text-sm text-gray-600 dark:text-gray-400">
              Digite seu email para receber as instruções de recuperação.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 px-6 pb-6 pt-0">
            {/* Mensagem de sucesso */}
            {success && (
              <div className="p-3 rounded-md bg-green-100 text-green-800 text-sm">
                Email enviado! Verifique sua caixa de entrada.
              </div>
            )}

            {/* Mensagem de erro */}
            {error && (
              <div className="p-3 rounded-md bg-red-100 text-red-800 text-sm">
                {error}
              </div>
            )}

            <div className="grid gap-3">
              <Label
                htmlFor="email"
                className="text-gray-700 dark:text-gray-300"
              >
                Email
              </Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="seu@email.com"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading || success}
                className="border-gray-300 dark:border-gray-600"
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading || success}>
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                "Enviar"
              )}
            </Button>
            <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
              <Link
                href="/login"
                className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-500"
              >
                Voltar ao login
              </Link>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
