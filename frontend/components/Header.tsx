"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LogIn, LogOut, ShieldUser, User, UserPlus, FolderOpen } from "lucide-react";

// ===============================
// Tipo para os dados do usuário extraídos do token JWT
// ===============================
type UserInfo = {
  username: string;
  email: string;
  is_admin: boolean;
};

// ===============================
// PLACEHOLDER (COMENTADO) - Dados estáticos antigos
// ===============================
// const loggedUser = {
//   name: "João Silva",
//   isLoggedIn: true,
//   isAdmin: true,
// };

export function Header() {
  const router = useRouter();
  
  // ===============================
  // Estados para controlar o usuário logado
  // ===============================
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Evita flash de UI

  // ===============================
  // useEffect: Busca dados do usuário via API /users/me
  // ===============================
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Pega o token do localStorage
        const token = localStorage.getItem("access_token");
        
        if (token) {
          // Busca os dados completos do usuário via API
          const response = await fetch("http://localhost:8000/users/me", {
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const userData = await response.json();
            setUser({
              username: userData.username,
              email: userData.email,
              is_admin: userData.is_admin,
            });
            setIsLoggedIn(true);
          } else {
            // Token inválido ou expirado
            localStorage.removeItem("access_token");
            localStorage.removeItem("token_type");
            setIsLoggedIn(false);
            setUser(null);
          }
        } else {
          setIsLoggedIn(false);
          setUser(null);
        }
      } catch (error) {
        console.error("Erro ao verificar autenticação:", error);
        setIsLoggedIn(false);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
    
    // Escuta mudanças no localStorage (para atualizar quando fizer login/logout em outra aba)
    window.addEventListener("storage", checkAuth);
    
    // Escuta evento customizado de mudança de autenticação (para atualizar na mesma aba)
    window.addEventListener("auth-change", checkAuth);
    
    return () => {
      window.removeEventListener("storage", checkAuth);
      window.removeEventListener("auth-change", checkAuth);
    };
  }, []);

  // ===============================
  // Função de logout
  // ===============================
  const handleLogout = () => {
    // Remove os tokens do localStorage
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    
    // Atualiza o estado
    setIsLoggedIn(false);
    setUser(null);
    
    // Redireciona para a página inicial
    router.push("/");
  };

  // Não renderiza nada enquanto verifica autenticação (evita flash)
  if (isLoading) {
    return (
      <header className="border-b bg-background">
        <div className="flex h-14 items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded bg-primary flex items-center justify-center">
              <span className="text-green-foreground font-bold text-sm">CN</span>
            </div>
            <span className="font-semibold text-lg">ChatNext</span>
          </Link>
        </div>
      </header>
    );
  }

  return (
    <header className="border-b bg-background">
      <div className="flex h-14 items-center justify-between px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded bg-green-800 flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">CN</span>
          </div>
          <span className="font-semibold text-lg">ChatNext</span>
        </Link>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {isLoggedIn && user ? (
            <>
              {/* User name */}
              <Link href="/profile" className="flex items-center gap-2 text-sm hover:text-primary transition-colors">
                <User className="h-4 w-4 text-muted-foreground" />
                <span>{user.username}</span>
              </Link>

              {/* Projects link */}
              <Link href="/projects">
                <Button variant="ghost" size="icon" title="Meus Projetos" className="cursor-pointer">
                  <FolderOpen className="h-4 w-4 text-green-700" />
                </Button>
              </Link>

              {/* Admin area - só aparece se is_admin for true */}
              {user.is_admin && (
                <Link href="/admin/users">
                  <Button variant="ghost" size="icon" title="Área Administrativa" className="cursor-pointer">
                    <ShieldUser className="h-4 w-4 text-amber-700" />
                  </Button>
                </Link>
              )}

              {/* Logout */}
              <Button variant="ghost" size="icon" title="Sair" onClick={handleLogout} className="cursor-pointer">
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <Link href="/register">
                <Button variant="ghost" size="sm" className="cursor-pointer">
                  <UserPlus className="h-4 w-4 mr-2" />
                  Cadastrar
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="ghost" size="sm" className="cursor-pointer">
                  <LogIn className="h-4 w-4 mr-2" />
                  Entrar
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
