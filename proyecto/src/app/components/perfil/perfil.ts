import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth';
import { UsuarioService } from '../../services/usuario';
import { SelectorUbicacion, UbicacionService } from '../../services/ubicacion';
import { PROVINCIAS_ARGENTINAS } from '../../data/provincias';
import { finalize } from 'rxjs';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule],
  selector: 'app-perfil',
  templateUrl: './perfil.html',
  styleUrl: './perfil.css',
})
export class Perfil implements OnInit {
  readonly provincias = PROVINCIAS_ARGENTINAS;
  idUsuario: number | null = null;
  nombre = '';
  email = '';
  telefono = '';
  descripcion = '';
  calle = '';
  numero = '';
  piso = '';
  ubicacion: SelectorUbicacion;
  // Lo que se muestra arriba: la ubicación guardada, no la que se está editando.
  ubicacionTexto = 'Sin ubicación cargada';
  fotoPerfil = '';
  ocultarTelefono = true;
  // Privada por defecto. Se guarda en el back (direccion_publica) y decide si la
  // calle, número y piso se ven en el perfil público.
  ocultarDireccion = true;
  guardandoPrivacidad = false;
  cargando = true;
  guardando = false;
  cambiandoPassword = false;
  mostrarCambioPassword = false;
  errorCarga = false;
  passwordActual = '';
  passwordNuevo = '';
  confirmarPasswordNuevo = '';

  constructor(
    private usuarios: UsuarioService,
    private ubicaciones: UbicacionService,
    private auth: AuthService,
    private toastr: ToastrService,
    private router: Router,
    private changeDetector: ChangeDetectorRef
  ) {
    this.ubicacion = new SelectorUbicacion(this.ubicaciones, () => this.changeDetector.detectChanges());
  }

  ngOnInit(): void {
    this.ocultarTelefono = localStorage.getItem('perfil-ocultar-telefono') !== 'false';
    const usuario = this.auth.getUsuarioActual();
    if (!usuario?.id_usuario) {
      this.cargando = false;
      this.errorCarga = true;
      return;
    }
    this.idUsuario = usuario.id_usuario;
    this.fotoPerfil = this.obtenerFotoPerfil(usuario.id_usuario);
    this.cargarPerfil(usuario);
  }

  guardar(): void {
    if (!this.idUsuario || this.guardando) {
      return;
    }
    if (!this.ubicacion.completa) {
      this.toastr.warning('Elegí provincia, departamento y localidad.');
      return;
    }
    if (!this.calle.trim() || !this.numeroValido) {
      this.toastr.warning('Completá la calle y el número (solo dígitos).');
      return;
    }

    this.guardando = true;
    this.usuarios.update(this.idUsuario, {
      nombre_completo: this.nombre.trim(),
      email: this.email.trim(),
      telefono: this.telefono.trim(),
      descripcion: this.descripcion.trim(),
      provincia: this.ubicacion.provincia,
      departamento: this.ubicacion.departamento,
      ciudad: this.ubicacion.ciudad,
      // Igual que en el registro, la zona aproximada es la ciudad.
      zona_aproximada: this.ubicacion.ciudad,
      calle: this.calle.trim(),
      numero: this.numero.trim(),
      piso: this.piso.trim() || null
    }).subscribe({
      next: response => {
        const actualizado = response?.data;
        if (!actualizado?.id_usuario) {
          this.guardando = false;
          this.toastr.error('El servidor no devolvió los datos actualizados.');
          return;
        }
        this.auth.actualizarUsuarioActual(actualizado);
        this.cargarCampos(actualizado);
        this.guardando = false;
        this.toastr.success('Tu perfil fue actualizado.');
      },
      error: error => {
        console.error('No se pudo actualizar el perfil.', error);
        this.toastr.error(this.errorMessage(error));
        this.guardando = false;
      }
    });
  }

  cambiarPassword(): void {
    if (!this.idUsuario || this.cambiandoPassword) {
      return;
    }
    if (this.passwordNuevo.length < 6) {
      this.toastr.warning('La nueva contraseña debe tener al menos 6 caracteres.');
      return;
    }
    if (this.passwordNuevo !== this.confirmarPasswordNuevo) {
      this.toastr.warning('Las contraseñas nuevas no coinciden.');
      return;
    }

    this.cambiandoPassword = true;
    this.usuarios.cambiarPassword(this.idUsuario, this.passwordActual, this.passwordNuevo).subscribe({
      next: () => {
        this.passwordActual = '';
        this.passwordNuevo = '';
        this.confirmarPasswordNuevo = '';
        this.mostrarCambioPassword = false;
        this.cambiandoPassword = false;
        this.toastr.success('Tu contraseña fue actualizada.');
      },
      error: error => {
        console.error('No se pudo cambiar la contraseña.', error);
        this.toastr.error(this.errorMessage(error));
        this.cambiandoPassword = false;
      }
    });
  }

  cambiarPrivacidadTelefono(value: boolean): void {
    this.ocultarTelefono = value;
    localStorage.setItem('perfil-ocultar-telefono', String(value));
    this.toastr.info('La preferencia se guardó en este navegador.');
  }

  get numeroValido(): boolean {
    return /^\d{1,6}$/.test(this.numero.trim());
  }

  /** Se guarda en el momento, sin tocar "Guardar cambios". */
  cambiarPrivacidadDireccion(ocultar: boolean): void {
    if (!this.idUsuario || this.guardandoPrivacidad) {
      return;
    }
    this.ocultarDireccion = ocultar;
    this.guardandoPrivacidad = true;
    this.usuarios.update(this.idUsuario, { direccion_publica: !ocultar }).subscribe({
      next: response => {
        this.guardandoPrivacidad = false;
        if (response?.data?.id_usuario) {
          this.auth.actualizarUsuarioActual(response.data);
        }
        this.toastr.success(ocultar
          ? 'Tu dirección quedó oculta en tu perfil público.'
          : 'Tu dirección ahora se ve en tu perfil público.');
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudo cambiar la privacidad de la dirección.', error);
        // Volvemos el interruptor a como estaba.
        this.ocultarDireccion = !ocultar;
        this.guardandoPrivacidad = false;
        this.toastr.error(this.errorMessage(error));
        this.changeDetector.detectChanges();
      }
    });
  }

  seleccionarFoto(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    if (!file.type.startsWith('image/')) {
      this.toastr.warning('Seleccioná un archivo de imagen.');
      input.value = '';
      return;
    }
    if (file.size > 3 * 1024 * 1024) {
      this.toastr.warning('La imagen no puede superar los 3 MB.');
      input.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        this.fotoPerfil = reader.result;
        try {
          if (!this.idUsuario) {
            throw new Error('No hay una cuenta activa para asociar la foto.');
          }
          localStorage.setItem(`perfil-foto-${this.idUsuario}`, reader.result);
          this.toastr.success('Foto actualizada en este navegador.');
        } catch (error) {
          console.error('No se pudo guardar la foto en el navegador.', error);
          this.toastr.warning('La vista previa cambió, pero no se pudo guardar en este navegador.');
        }
      }
    };
    reader.onerror = () => this.toastr.error('No se pudo leer la imagen seleccionada.');
    reader.readAsDataURL(file);
    input.value = '';
  }

  private obtenerFotoPerfil(userId: number): string {
    try {
      const key = `perfil-foto-${userId}`;
      const fotoGuardada = localStorage.getItem(key);
      if (fotoGuardada) {
        return fotoGuardada;
      }
      const fotoAnterior = localStorage.getItem('perfil-foto');
      if (fotoAnterior) {
        localStorage.setItem(key, fotoAnterior);
        localStorage.removeItem('perfil-foto');
      }
      return fotoAnterior || '';
    } catch (error) {
      console.error('No se pudo leer la foto de perfil guardada en este navegador.', error);
      return '';
    }
  }

  private cargarPerfil(usuario: any): void {
    this.cargarCampos(usuario);
    this.usuarios.get(usuario.id_usuario).pipe(
      finalize(() => {
        this.cargando = false;
        this.changeDetector.detectChanges();
      })
    ).subscribe({
      next: response => {
        if (response?.data) {
          this.cargarCampos(response.data);
          this.auth.actualizarUsuarioActual(response.data);
        }
      },
      error: error => {
        if (error.status === 404) {
          console.warn('La sesión guardada apunta a una cuenta que ya no existe.');
          this.auth.logout();
          this.errorCarga = true;
          this.toastr.warning('Tu sesión pertenece a una cuenta que ya no existe. Iniciá sesión con tu cuenta actual.');
          this.router.navigate(['/login'], { queryParams: { returnUrl: '/perfil' } });
          return;
        }
        console.error('No se pudo consultar el perfil actualizado; se muestran los datos de sesión.', error);
      }
    });
  }

  private cargarCampos(usuario: any): void {
    this.nombre = usuario?.nombre_completo ?? '';
    this.email = usuario?.email ?? '';
    this.telefono = usuario?.telefono ?? '';
    this.descripcion = usuario?.descripcion ?? '';
    this.ocultarDireccion = !usuario?.direccion_publica;
    const ubicacion = usuario?.ubicacion;
    // Los que se registraron antes de separar la dirección no tienen calle ni número:
    // tienen que completarlos una vez.
    this.calle = ubicacion?.calle ?? '';
    this.numero = ubicacion?.numero ?? '';
    this.piso = ubicacion?.piso ?? '';
    this.ubicacionTexto = [ubicacion?.ciudad, ubicacion?.provincia].filter(Boolean).join(', ')
      || 'Sin ubicación cargada';
    // Si el usuario se registró antes de que existiera el departamento, queda
    // la provincia elegida y tiene que completar departamento y localidad.
    this.ubicacion.cargar(ubicacion?.provincia ?? '', ubicacion?.departamento ?? '', ubicacion?.ciudad ?? '');
  }

  private errorMessage(error: any): string {
    const data = error?.error?.data;
    if (typeof data === 'string') {
      return data;
    }
    if (data && typeof data === 'object') {
      return Object.values(data).flat().join(' ') || 'No se pudo guardar el perfil.';
    }
    return 'No se pudo guardar el perfil. Revisá la conexión con el servidor.';
  }
}
