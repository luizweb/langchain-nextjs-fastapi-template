"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableHeader,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { MoreHorizontal, Plus, Shield, User, Loader2, ChevronLeft, ChevronRight } from "lucide-react";

// ===============================
// DADOS PLACEHOLDER (COMENTADO)
// ===============================
// const initialUsers = [
//   {
//     id: 1,
//     name: "João Silva",
//     email: "joao.silva@email.com",
//     role: "admin",
//     status: "active",
//     createdAt: "2024-01-15",
//   },
//   {
//     id: 2,
//     name: "Maria Santos",
//     email: "maria.santos@email.com",
//     role: "user",
//     status: "active",
//     createdAt: "2024-02-20",
//   },
//   {
//     id: 3,
//     name: "Pedro Oliveira",
//     email: "pedro.oliveira@email.com",
//     role: "user",
//     status: "inactive",
//     createdAt: "2024-03-10",
//   },
//   {
//     id: 4,
//     name: "Ana Costa",
//     email: "ana.costa@email.com",
//     role: "user",
//     status: "active",
//     createdAt: "2024-04-05",
//   },
//   {
//     id: 5,
//     name: "Carlos Ferreira",
//     email: "carlos.ferreira@email.com",
//     role: "admin",
//     status: "active",
//     createdAt: "2024-05-12",
//   },
// ];

// ===============================
// PASSO 1: Definir o tipo conforme a resposta da API
// A API retorna: {"users":[{"id":1,"username":"luizweb","email":"luizweb@example.com","is_admin":true}]}
// ===============================
type UserType = {
  id: number;
  username: string;   // API retorna username ao invés de name
  email: string;
  is_admin: boolean;  // API retorna is_admin (boolean) ao invés de role (string)
  created_at: string; // Data de criação
  updated_at: string; // Data de atualização
};

// Tipo para a resposta completa da API
type ApiResponse = {
  users: UserType[];
};

export default function AdminUsersPage() {
  const router = useRouter();
  
  // ===============================
  // Estados para autenticação e autorização
  // ===============================
  const [isAuthChecking, setIsAuthChecking] = useState(true);  // Verificando permissões
  
  // ===============================
  // PASSO 2: Estados para gerenciar dados, loading e erros
  // ===============================
  const [users, setUsers] = useState<UserType[]>([]);        // Lista de usuários da API
  const [isLoading, setIsLoading] = useState(true);          // Estado de carregamento
  const [error, setError] = useState<string | null>(null);   // Estado de erro
  const [deletingUser, setDeletingUser] = useState<UserType | null>(null);
  
  // Estados para o modal de criação de usuário
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newIsAdmin, setNewIsAdmin] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  
  // Estados para paginação
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10; // Quantidade de itens por página

  // ===============================
  // VERIFICAÇÃO DE AUTENTICAÇÃO E AUTORIZAÇÃO
  // Este useEffect verifica se o usuário:
  // 1. Está logado (possui token)
  // 2. É administrador (is_admin = true)
  // ===============================
  useEffect(() => {
    const checkAuthorization = async () => {
      try {
        // PASSO 1: Verifica se existe token no localStorage
        const token = localStorage.getItem("access_token");
        
        if (!token) {
          // Usuário não está logado - redireciona para login
          console.log("Acesso negado: Usuário não está logado");
          router.push("/login");
          return;
        }

        // PASSO 2: Busca dados do usuário para verificar se é admin
        const response = await fetch("http://localhost:8000/users/me", {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          // Token inválido ou expirado - limpa e redireciona
          console.log("Acesso negado: Token inválido ou expirado");
          localStorage.removeItem("access_token");
          localStorage.removeItem("token_type");
          router.push("/login");
          return;
        }

        const userData = await response.json();

        // PASSO 3: Verifica se o usuário é administrador
        if (!userData.is_admin) {
          // Usuário não é admin - redireciona para página inicial
          console.log("Acesso negado: Usuário não é administrador");
          router.push("/");
          return;
        }

        // PASSO 4: Usuário autorizado - permite acesso à página
        console.log("Acesso permitido: Usuário é administrador");
        setIsAuthChecking(false);
        
      } catch (error) {
        console.error("Erro ao verificar autorização:", error);
        router.push("/login");
      }
    };

    checkAuthorization();
  }, [router]);

  // ===============================
  // PASSO 3: useEffect para buscar dados da API quando autorizado
  // ===============================
  useEffect(() => {
    // Só busca usuários se já passou na verificação de autorização
    if (isAuthChecking) return;
    
    const fetchUsers = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // PASSO 3.1: Faz a requisição GET para a API
        const response = await fetch("http://localhost:8000/users/");
        
        // PASSO 3.2: Verifica se a resposta foi bem sucedida
        if (!response.ok) {
          throw new Error(`Erro ao carregar usuários: ${response.status}`);
        }
        
        // PASSO 3.3: Converte a resposta para JSON
        const data: ApiResponse = await response.json();
        
        // PASSO 3.4: Atualiza o estado com os usuários recebidos
        console.log("=== DADOS DA API ===");
        console.log(data.users);
        console.log("====================");
        setUsers(data.users);
      } catch (err) {
        // PASSO 3.5: Em caso de erro, salva a mensagem de erro
        setError(err instanceof Error ? err.message : "Erro desconhecido");
      } finally {
        // PASSO 3.6: Finaliza o loading independente do resultado
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, [isAuthChecking]); // Executa quando a verificação de autorização terminar

  const handleDeleteClick = (user: UserType) => {
    setDeletingUser(user);
  };

  // ===============================
  // Função para criar novo usuário (POST)
  // ===============================
  const handleCreateUser = async () => {
    // Validações
    if (!newUsername || !newEmail || !newPassword) {
      setCreateError("Preencha todos os campos");
      return;
    }

    if (newPassword.length < 6) {
      setCreateError("A senha deve ter pelo menos 6 caracteres");
      return;
    }

    try {
      setIsCreating(true);
      setCreateError(null);
      
      const token = localStorage.getItem("access_token");
      
      const response = await fetch("http://localhost:8000/users/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          username: newUsername,
          email: newEmail,
          password: newPassword,
          is_admin: newIsAdmin,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao criar usuário");
      }

      const newUser = await response.json();
      
      // Adiciona o novo usuário à lista
      setUsers([...users, newUser]);
      
      // Limpa o formulário e fecha o modal
      setNewUsername("");
      setNewEmail("");
      setNewPassword("");
      setNewIsAdmin(false);
      setIsCreateModalOpen(false);
      
      console.log("Usuário criado com sucesso:", newUser);
      
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Erro ao criar usuário");
    } finally {
      setIsCreating(false);
    }
  };

  // Limpa o formulário ao fechar o modal
  const handleCloseCreateModal = (open: boolean) => {
    if (!open) {
      setNewUsername("");
      setNewEmail("");
      setNewPassword("");
      setNewIsAdmin(false);
      setCreateError(null);
    }
    setIsCreateModalOpen(open);
  };

  // ===============================
  // PASSO 4: Função de exclusão que chama a API DELETE
  // ===============================
  const handleConfirmDelete = async () => {
    if (!deletingUser) return;
    
    try {
      // Pega o token para autenticação
      const token = localStorage.getItem("access_token");
      
      // Faz a requisição DELETE para a API
      const response = await fetch(`http://localhost:8000/users/${deletingUser.id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao excluir usuário");
      }

      // Sucesso: Remove o usuário da lista local
      setUsers(users.filter(u => u.id !== deletingUser.id));
      console.log("Usuário excluído com sucesso:", deletingUser);
      
    } catch (err) {
      // Em caso de erro, mostra no console
      console.error("Erro ao excluir usuário:", err);
      setError(err instanceof Error ? err.message : "Erro ao excluir usuário");
    } finally {
      setDeletingUser(null);
    }
  };

  // ===============================
  // LOADING STATE: Enquanto verifica permissões
  // ===============================
  if (isAuthChecking) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Verificando permissões...</span>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Administração de Usuários</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gerencie os usuários do sistema
          </p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)} className="cursor-pointer">
          <Plus className="h-4 w-4 mr-2" />
          Novo Usuário
        </Button>
      </div>

      <section className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium">Usuários</h2>
          <span className="text-sm text-muted-foreground">
            {users.length} usuário{users.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* ===============================
            PASSO 5: Renderização condicional baseada nos estados
            =============================== */}
        
        {/* PASSO 5.1: Exibe loading enquanto carrega */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Carregando usuários...</span>
          </div>
        )}

        {/* PASSO 5.2: Exibe erro se houver */}
        {error && (
          <div className="flex items-center justify-center py-12 text-destructive">
            <p>Erro: {error}</p>
          </div>
        )}

        {/* PASSO 5.3: Exibe a tabela se não estiver carregando e não houver erro */}
        {!isLoading && !error && (
          <Table className="text-sm">
            <TableHeader>
              <TableRow className="border-b border-gray-100 hover:bg-transparent">
                <TableHead className="w-[50px] text-xs font-medium text-muted-foreground">ID</TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground">Nome</TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground">Email</TableHead>
                <TableHead className="text-center text-xs font-medium text-muted-foreground">Perfil</TableHead>
                <TableHead className="text-center text-xs font-medium text-muted-foreground">Criado em</TableHead>
                <TableHead className="text-center text-xs font-medium text-muted-foreground">Atualizado em</TableHead>
                <TableHead className="w-[60px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    Nenhum usuário encontrado
                  </TableCell>
                </TableRow>
              ) : (
                // Paginação: filtra os usuários da página atual
                users
                  .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                  .map((user) => (
                  <TableRow key={user.id} className="border-b border-gray-100 hover:bg-gray-200">
                    {/* PASSO 6: Adaptação dos campos para o formato da API */}
                    <TableCell className="text-muted-foreground">{user.id}</TableCell>
                    <TableCell className="font-medium">{user.username}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell className="text-center">
                      {/* is_admin é boolean, então verificamos diretamente */}
                      <Badge variant={user.is_admin ? "default" : "secondary"}>
                        {user.is_admin ? (
                          <Shield className="h-3 w-3 mr-1" />
                        ) : (
                          <User className="h-3 w-3 mr-1" />
                        )}
                        {user.is_admin ? "Admin" : "Usuário"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center text-sm text-muted-foreground">
                      {user.created_at ? user.created_at.split(' ')[0].split('-').reverse().join('/') : '-'}
                    </TableCell>
                    <TableCell className="text-center text-sm text-muted-foreground">
                      {user.updated_at ? user.updated_at.split(' ')[0].split('-').reverse().join('/') : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>Editar</DropdownMenuItem>
                          <DropdownMenuItem>Alterar Perfil</DropdownMenuItem>
                          <DropdownMenuItem 
                            className="text-destructive"
                            onClick={() => handleDeleteClick(user)}
                          >
                            Excluir
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}

        {/* Paginação */}
        {!isLoading && !error && users.length > 0 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
            <span className="text-sm text-muted-foreground">
              Mostrando {Math.min((currentPage - 1) * itemsPerPage + 1, users.length)} a {Math.min(currentPage * itemsPerPage, users.length)} de {users.length} registros
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="h-8"
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Anterior
              </Button>
              <span className="text-sm px-2">
                Página {currentPage} de {Math.ceil(users.length / itemsPerPage) || 1}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.min(Math.ceil(users.length / itemsPerPage), p + 1))}
                disabled={currentPage >= Math.ceil(users.length / itemsPerPage)}
                className="h-8"
              >
                Próxima
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        )}
      </section>

      {/* Dialog de Criação de Usuário */}
      <Dialog open={isCreateModalOpen} onOpenChange={handleCloseCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Novo Usuário</DialogTitle>
            <DialogDescription>
              Preencha os dados para criar um novo usuário.
            </DialogDescription>
          </DialogHeader>
          
          {/* Mensagem de erro */}
          {createError && (
            <div className="p-3 rounded-md bg-red-100 text-red-800 text-sm">
              {createError}
            </div>
          )}
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="newUsername">Nome de usuário</Label>
              <Input
                id="newUsername"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                placeholder="nome_usuario"
                disabled={isCreating}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="newEmail">Email</Label>
              <Input
                id="newEmail"
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="email@exemplo.com"
                disabled={isCreating}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="newPassword">Senha</Label>
              <Input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Mínimo 6 caracteres"
                disabled={isCreating}
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="newIsAdmin"
                checked={newIsAdmin}
                onChange={(e) => setNewIsAdmin(e.target.checked)}
                disabled={isCreating}
                className="h-4 w-4 rounded border-gray-300 cursor-pointer"
              />
              <Label htmlFor="newIsAdmin" className="cursor-pointer">
                Administrador
              </Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => handleCloseCreateModal(false)}
              disabled={isCreating}
            >
              Cancelar
            </Button>
            <Button onClick={handleCreateUser} disabled={isCreating}>
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Criando...
                </>
              ) : (
                "Criar Usuário"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AlertDialog de Exclusão */}
      <AlertDialog open={!!deletingUser} onOpenChange={(open) => !open && setDeletingUser(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Usuário</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir o usuário <strong>"{deletingUser?.username}"</strong> ({deletingUser?.email})?
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
