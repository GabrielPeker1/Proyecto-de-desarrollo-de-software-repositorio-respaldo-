import { Routes } from '@angular/router';
import { PublicacionList } from './components/publicacion-list/publicacion-list';
import { PublicacionDetail } from './components/publicacion-detail/publicacion-detail';
import { PublicacionAdd } from './components/publicacion-add/publicacion-add';
import { Login } from './components/login/login';
import { Registro } from './components/registro/registro';
import { SolicitudList } from './components/solicitud-list/solicitud-list';
import { ChatList } from './components/chat-list/chat-list';
import { ChatDetail } from './components/chat-detail/chat-detail';
import { Perfil } from './components/perfil/perfil';
import { PerfilPublicoComponent } from './components/perfil-publico/perfil-publico';
import { authenticatedOnlyGuard, rescuerOnlyGuard } from './guards/role.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'publicaciones', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'registro', component: Registro },
  { path: 'publicaciones', component: PublicacionList, canActivate: [authenticatedOnlyGuard] },
  { path: 'publicaciones/:id', component: PublicacionDetail, canActivate: [authenticatedOnlyGuard] },
  { path: 'publicar', component: PublicacionAdd, canActivate: [authenticatedOnlyGuard, rescuerOnlyGuard] },
  { path: 'solicitudes', component: SolicitudList, canActivate: [authenticatedOnlyGuard] },
  { path: 'chats', component: ChatList, canActivate: [authenticatedOnlyGuard] },
  { path: 'chats/:id', component: ChatDetail, canActivate: [authenticatedOnlyGuard] },
  { path: 'perfil', component: Perfil, canActivate: [authenticatedOnlyGuard] },
  { path: 'usuarios/:id', component: PerfilPublicoComponent, canActivate: [authenticatedOnlyGuard] },
  { path: '**', redirectTo: 'publicaciones' }
];