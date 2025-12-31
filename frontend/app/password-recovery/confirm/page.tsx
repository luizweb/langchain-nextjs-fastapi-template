"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams, notFound } from "next/navigation";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

// ===============================
// EXPLICAÇÃO: O que é /password-recovery/confirm?
// ===============================
// Este é o segundo passo do fluxo de recuperação de senha:
//
// FLUXO COMPLETO:
// 1. Usuário acessa /password-recovery e digita seu email
// 2. Sistema envia um email com link: /password-recovery/confirm?token=abc123
// 3. Usuário clica no link e é redirecionado para esta página
// 4. Esta página lê o token da URL (query param) para validar a requisição
// 5. Usuário digita a nova senha e confirma
// 6. Sistema valida o token e atualiza a senha no banco
//
// O TOKEN garante que:
// - Apenas quem tem acesso ao email pode redefinir a senha
// - O link expira após um tempo (ex: 1 hora)
// - Cada token só pode ser usado uma vez
// ===============================

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  // Se não há token na URL, página não encontrada
  if (!token) {
    notFound();
  }

  // Estados do formulário
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Placeholder: Função para redefinir a senha
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validação
    if (password !== confirmPassword) {
      setError("As senhas não coincidem");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Implementar chamada à API para redefinir senha
      // await fetch("http://localhost:8000/auth/password-reset/confirm", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify({ token, password }),
      // });
      
      console.log("Senha redefinida com token:", token);
      setSuccess(true);
      
      // Redireciona para login após 2 segundos
      setTimeout(() => {
        router.push("/login");
      }, 2000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao redefinir senha");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm">
      <Card className="w-full rounded-lg shadow-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-xl font-semibold text-gray-800 dark:text-white">
            Redefinir Senha
          </CardTitle>
          <CardDescription className="text-sm text-gray-600 dark:text-gray-400">
            Digite sua nova senha e confirme.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 px-6 pb-6 pt-0">
          {/* Mensagem de sucesso */}
          {success && (
            <div className="p-3 rounded-md bg-green-100 text-green-800 text-sm">
              Senha redefinida! Redirecionando para login...
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
              htmlFor="password"
              className="text-gray-700 dark:text-gray-300"
            >
              Nova Senha
            </Label>
            <Input
              id="password"
              name="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading || success}
              className="border-gray-300 dark:border-gray-600"
            />
          </div>
          <div className="grid gap-3">
            <Label
              htmlFor="confirmPassword"
              className="text-gray-700 dark:text-gray-300"
            >
              Confirmar Nova Senha
            </Label>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading || success}
              className="border-gray-300 dark:border-gray-600"
            />
          </div>
          <Button type="submit" className="w-full" disabled={isLoading || success}>
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Redefinindo...
              </>
            ) : (
              "Redefinir Senha"
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
  );
}

export default function Page() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Suspense fallback={
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Carregando...
        </div>
      }>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
