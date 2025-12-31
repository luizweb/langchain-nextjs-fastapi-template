"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { User, Trash2, Loader2 } from "lucide-react";

// ===============================
// PLACEHOLDER (COMENTADO) - Dados estáticos antigos
// ===============================
// const user = {
//   name: "João Silva",
//   email: "joao.silva@email.com",
// };

// Tipo para dados do usuário
type UserData = {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
};

export default function ProfilePage() {
  const router = useRouter();
  
  // Estados para os dados do usuário
  const [userId, setUserId] = useState<number | null>(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // Estados para loading/erro/sucesso
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // ===============================
  // Carrega os dados do usuário via API GET /users/me
  // ===============================
  useEffect(() => {
    const loadUserData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        
        if (!token) {
          router.push("/login");
          return;
        }
        
        // Busca os dados do usuário logado via API
        const response = await fetch("http://localhost:8000/users/me", {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          if (response.status === 401) {
            // Token inválido ou expirado
            localStorage.removeItem("access_token");
            localStorage.removeItem("token_type");
            router.push("/login");
            return;
          }
          throw new Error("Erro ao carregar dados do perfil");
        }

        const userData: UserData = await response.json();
        
        setUserId(userData.id);
        setUsername(userData.username);
        setEmail(userData.email);
        
      } catch (error) {
        console.error("Erro ao carregar dados do usuário:", error);
        setError("Erro ao carregar dados do perfil");
      } finally {
        setIsLoading(false);
      }
    };

    loadUserData();
  }, [router]);

  // ===============================
  // Função para atualizar o perfil (PUT)
  // ===============================
  const handleUpdateProfile = async () => {
    // Validação - senha é obrigatória para atualizar o perfil
    if (!password) {
      setError("Digite sua senha para confirmar as alterações");
      return;
    }

    if (password !== confirmPassword) {
      setError("As senhas não coincidem");
      return;
    }

    if (!userId) {
      setError("ID do usuário não encontrado");
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      setSuccess(null);
      
      const token = localStorage.getItem("access_token");
      
      // Monta o body da requisição (API exige todos os campos incluindo password)
      const body = {
        username,
        email,
        password,
        is_admin: false, // Mantém o valor atual ou define como false
      };
      
      const response = await fetch(`http://localhost:8000/users/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json();
        // Trata diferentes formatos de erro da API
        let errorMessage = "Erro ao atualizar perfil";
        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((e: { msg: string }) => e.msg).join(", ");
        }
        throw new Error(errorMessage);
      }

      // Limpa os campos de senha após sucesso
      setPassword("");
      setConfirmPassword("");
      setSuccess("Perfil atualizado com sucesso!");
      
      // Dispara evento para atualizar o Header se o username mudou
      window.dispatchEvent(new Event("auth-change"));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar perfil");
    } finally {
      setIsSaving(false);
    }
  };

  // ===============================
  // Função para excluir a conta (DELETE)
  // ===============================
  const handleDeleteAccount = async () => {
    if (!userId) {
      setError("ID do usuário não encontrado");
      return;
    }

    try {
      setIsDeleting(true);
      setError(null);
      
      const token = localStorage.getItem("access_token");
      
      const response = await fetch(`http://localhost:8000/users/${userId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao excluir conta");
      }

      // Limpa o localStorage e redireciona
      localStorage.removeItem("access_token");
      localStorage.removeItem("token_type");
      
      // Dispara evento para atualizar o Header
      window.dispatchEvent(new Event("auth-change"));
      
      // Redireciona para a página inicial
      router.push("/");
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir conta");
      setShowDeleteDialog(false);
    } finally {
      setIsDeleting(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Carregando perfil...</span>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Meu Perfil</h1>

      {/* Mensagens de erro/sucesso globais */}
      {error && (
        <div className="mb-4 p-3 rounded-md bg-red-100 text-red-800 text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 rounded-md bg-green-100 text-green-800 text-sm">
          {success}
        </div>
      )}

      {/* Edit Profile Card */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center">
              <User className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <CardTitle>Editar Perfil</CardTitle>
              <CardDescription>Atualize suas informações pessoais</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Nome de usuário</Label>
            <Input 
              id="username" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Seu nome de usuário"
              disabled={isSaving}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input 
              id="email" 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              disabled={isSaving}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Senha</Label>
            <Input 
              id="password" 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Digite sua senha"
              disabled={isSaving}
            />
            <p className="text-xs text-muted-foreground">
              Obrigatório para confirmar as alterações
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirmar Senha</Label>
            <Input 
              id="confirmPassword" 
              type="password" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirme sua senha"
              disabled={isSaving}
            />
          </div>
        </CardContent>
        <CardFooter>
          <Button onClick={handleUpdateProfile} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : (
              "Salvar Alterações"
            )}
          </Button>
        </CardFooter>
      </Card>

      {/* Delete Account Card */}
      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">Zona de Perigo</CardTitle>
          <CardDescription>
            Ações irreversíveis para sua conta
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Ao excluir sua conta, todos os seus dados serão permanentemente removidos. 
            Esta ação não pode ser desfeita.
          </p>
          <Button 
            variant="destructive" 
            onClick={() => setShowDeleteDialog(true)}
            disabled={isDeleting}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Excluir Conta
          </Button>
        </CardContent>
      </Card>

      {/* AlertDialog de confirmação de exclusão */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Conta</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir sua conta? Todos os seus dados serão permanentemente removidos.
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteAccount}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Excluindo...
                </>
              ) : (
                "Excluir Conta"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
