import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth_service';
import { StorageService } from '../../services/storage.service';
import QRCode from 'qrcode';

interface TicketView {
  token: string;
  ubs: string;
  validoAte: Date;
  expirado: boolean;
}

@Component({
  selector: 'app-patient-ticket',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './patient-ticket.component.html',
  styleUrl: './patient-ticket.component.css',
})
export class PatientTicketComponent implements OnInit {
  private readonly auth    = inject(AuthService);
  private readonly storage = inject(StorageService);
  private readonly router  = inject(Router);

  protected readonly carregando = signal(true);
  protected readonly ticketView = signal<TicketView | null>(null);
  protected readonly qrDataUrl  = signal<string>('');

  protected readonly rotaUrl = computed(() => {
    const t = this.ticketView();
    if (!t) return '#';
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(t.ubs)}`;
  });

  ngOnInit(): void {
    const uid = this.auth.currentUser()?.id;
    if (!uid) { this.carregando.set(false); return; }

    this.storage.buscarPacientePorUsuario(uid).subscribe({
      next: (paciente) => {
        this.storage.historicoTriagens(paciente.id).subscribe({
          next: (triagens) => {
            // Pega a triagem mais recente que tem ticket associado
            const comTicket = triagens
              .filter(t => !!t.ticket)
              .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

            if (comTicket.length === 0) {
              this.carregando.set(false);
              return;
            }

            const triagem = comTicket[0];
            const ticket  = triagem.ticket!;
            const validoAte = new Date(ticket.valido_ate);
            const expirado  = new Date() > validoAte || ticket.status === 'expirado';
            const token     = `SUS-${ticket.id.slice(0, 6).toUpperCase()}`;

            this.ticketView.set({ token, ubs: ticket.ubs_encaminhamento, validoAte, expirado });
            this.carregando.set(false);
            this.gerarQrCode(token, ticket.ubs_encaminhamento, paciente.carteira_sus);
          },
          error: () => this.carregando.set(false),
        });
      },
      error: () => this.carregando.set(false),
    });
  }

  private async gerarQrCode(token: string, ubs: string, cns: string): Promise<void> {
    const conteudo = `${token}|${ubs}|${cns}`;
    try {
      const url = await QRCode.toDataURL(conteudo, {
        width: 220,
        margin: 2,
        color: { dark: '#1a1a2e', light: '#ffffff' },
        errorCorrectionLevel: 'M',
      });
      this.qrDataUrl.set(url);
    } catch {
      // ticket ainda é exibido sem QR
    }
  }

  protected aproximarDoTotem(): void {
    this.router.navigate(['/paciente/checkin']);
  }
}
