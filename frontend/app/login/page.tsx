"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
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

// ===============================
// PASSO 1: Tipo para a resposta do token da API
// A API retorna o access_token após login bem-sucedido
// ===============================
type TokenResponse = {
  access_token: string;
  token_type: string;
};

export default function Page() {
  const router = useRouter();
  
  // ===============================
  // PASSO 2: Estados para controlar o formulário
  // ===============================
  const [username, setUsername] = useState("");  // Email do usuário
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ===============================
  // PASSO 3: Função para enviar o login
  // ===============================
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsLoading(true);
      setError(null);
      
      // ===============================
      // PASSO 4: Preparar os dados para envio
      // OAuth2 espera dados em formato x-www-form-urlencoded
      // ===============================
      const formData = new URLSearchParams();
      formData.append("username", username);  // username é o email
      formData.append("password", password);
      
      // ===============================
      // PASSO 5: Fazer a requisição POST para /auth/token
      // ===============================
      const response = await fetch(`${API_URL}/auth/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      // ===============================
      // PASSO 6: Verificar se a resposta foi bem-sucedida
      // ===============================
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Credenciais inválidas");
      }

      // ===============================
      // PASSO 7: Extrair o token da resposta
      // ===============================
      const data: TokenResponse = await response.json();
      
      // ===============================
      // PASSO 8: Armazenar o token no localStorage
      // Obs: Em produção, considere usar httpOnly cookies para maior segurança
      // ===============================
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("token_type", data.token_type);
      
      // ===============================
      // PASSO 8.1: Disparar evento para atualizar o Header
      // O evento "storage" não é disparado na mesma aba, então usamos um evento customizado
      // ===============================
      window.dispatchEvent(new Event("auth-change"));
      
      // ===============================
      // PASSO 9: Redirecionar para a página de projetos
      // ===============================
      router.push("/projects");
      
    } catch (err) {
      // ===============================
      // PASSO 10: Tratar erros
      // ===============================
      setError(err instanceof Error ? err.message : "Erro ao fazer login");
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
              Login
            </CardTitle>
            <CardDescription className="text-sm text-gray-600 dark:text-gray-400">
              Entre com seu email para acessar sua conta.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 px-6 pb-6 pt-0">
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
                Email
              </Label>
              <Input
                id="username"
                name="username"
                type="email"
                placeholder="seu@email.com"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading}
                className="border-gray-300 dark:border-gray-600"
              />
            </div>
            <div className="grid gap-3">
              <div className="flex items-center justify-between">
                <Label
                  htmlFor="password"
                  className="text-gray-700 dark:text-gray-300"
                >
                  Senha
                </Label>
                <Link
                  href="/password-recovery"
                  className="text-sm text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-500"
                >
                  Esqueceu a senha?
                </Link>
              </div>
              <Input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className="border-gray-300 dark:border-gray-600"
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Entrando...
                </>
              ) : (
                "Entrar"
              )}
            </Button>
            <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
              Não tem uma conta?{" "}
              <Link
                href="/register"
                className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-500"
              >
                Cadastre-se
              </Link>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
