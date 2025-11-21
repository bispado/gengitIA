"""
Serviço de envio de emails
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Serviço para envio de emails"""
    
    async def send_meeting_invitation(
        self,
        candidate_email: str,
        candidate_name: str,
        meeting_date: str,
        meeting_time: str,
        meeting_type: str = "online",
        meeting_link: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Envia email de convite para reunião
        
        Args:
            candidate_email: Email do candidato
            candidate_name: Nome do candidato
            meeting_date: Data da reunião (YYYY-MM-DD)
            meeting_time: Hora da reunião (HH:MM)
            meeting_type: Tipo (online ou presencial)
            meeting_link: Link da reunião (se online)
            notes: Observações adicionais
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            # Criar mensagem
            message = MIMEMultipart("alternative")
            message["From"] = settings.email_from
            message["To"] = candidate_email
            message["Subject"] = f"Convite para Reunião - {candidate_name}"
            
            # Corpo do email
            if meeting_type == "online" and meeting_link:
                body_text = f"""
Olá {candidate_name},

Gostaríamos de convidá-lo(a) para uma reunião conosco.

Data: {meeting_date}
Hora: {meeting_time}
Tipo: Reunião Online

Link da reunião: {meeting_link}

{notes if notes else ''}

Aguardamos sua confirmação.

Atenciosamente,
Equipe de Recrutamento
"""
            else:
                body_text = f"""
Olá {candidate_name},

Gostaríamos de convidá-lo(a) para uma reunião presencial conosco.

Data: {meeting_date}
Hora: {meeting_time}
Tipo: Reunião Presencial

{notes if notes else ''}

Aguardamos sua confirmação.

Atenciosamente,
Equipe de Recrutamento
"""
            
            # Versão HTML
            body_html = f"""
<html>
  <body>
    <h2>Convite para Reunião</h2>
    <p>Olá <strong>{candidate_name}</strong>,</p>
    <p>Gostaríamos de convidá-lo(a) para uma reunião conosco.</p>
    <ul>
      <li><strong>Data:</strong> {meeting_date}</li>
      <li><strong>Hora:</strong> {meeting_time}</li>
      <li><strong>Tipo:</strong> {'Reunião Online' if meeting_type == 'online' else 'Reunião Presencial'}</li>
    </ul>
    {f'<p><strong>Link da reunião:</strong> <a href="{meeting_link}">{meeting_link}</a></p>' if meeting_link else ''}
    {f'<p>{notes}</p>' if notes else ''}
    <p>Aguardamos sua confirmação.</p>
    <p>Atenciosamente,<br>Equipe de Recrutamento</p>
  </body>
</html>
"""
            
            # Adicionar partes
            part1 = MIMEText(body_text, "plain")
            part2 = MIMEText(body_html, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Enviar email
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                use_tls=True
            )
            
            logger.info(f"Email enviado com sucesso para {candidate_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False


# Instância global do serviço de email
email_service = EmailService()

