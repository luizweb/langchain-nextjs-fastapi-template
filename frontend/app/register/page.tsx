"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/config";
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
import Link from "next/link";

export default function Page() {
  const router = useRouter();
  
  // Estados para os campos do formulário
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // Estados para loading, erro e sucesso
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Função para enviar o formulário
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validação: senhas devem coincidir
    if (password !== confirmPassword) {
      setError("As senhas não coincidem");
      return;
    }

    // Validação: senha deve ter pelo menos 6 caracteres
    if (password.length < 6) {
      setError("A senha deve ter pelo menos 6 caracteres");
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      // Faz a requisição POST para a API
      const response = await fetch(`${API_URL}/users/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          password,
          is_admin: false, // Usuários novos não são admin por padrão
        }),
      });

      // Verifica se a resposta foi bem sucedida
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erro ao criar usuário: ${response.status}`);
      }

      // Sucesso - mostra mensagem e redireciona
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm">
        <Card className="w-full rounded-lg shadow-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xl font-semibold text-gray-800 dark:text-white">
              Cadastrar
            </CardTitle>
            <CardDescription className="text-sm text-gray-600 dark:text-gray-400">
              Preencha os dados abaixo para criar sua conta.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 px-6 pb-6 pt-0">
            {/* Mensagem de sucesso */}
            {success && (
              <div className="p-3 rounded-md bg-green-100 text-green-800 text-sm">
                Conta criada com sucesso! Redirecionando para login...
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
                htmlFor="username"
                className="text-gray-700 dark:text-gray-300"
              >
                Nome de usuário
              </Label>
              <Input
                id="username"
                name="username"
                type="text"
                placeholder="Nome"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading || success}
                className="border-gray-300 dark:border-gray-600"
              />
            </div>
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
            <div className="grid gap-3">
              <Label
                htmlFor="password"
                className="text-gray-700 dark:text-gray-300"
              >
                Senha
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
                Confirmar Senha
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
                  Cadastrando...
                </>
              ) : (
                "Cadastrar"
              )}
            </Button>
            <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
              Já tem uma conta?{" "}
              <Link
                href="/login"
                className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-500"
              >
                Fazer login
              </Link>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
