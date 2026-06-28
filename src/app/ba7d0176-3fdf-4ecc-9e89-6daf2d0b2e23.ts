import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';

import { App } from './app';
import { routes } from './app.routes';
import { HeaderComponent } from './features/header-component/header.component';
import { SidebarComponent } from './features/sidebar-component/sidebar.component';

@NgModule({
  declarations: [ // Standalone components should not be declared here
  ],
  imports: [
    BrowserModule,
    RouterModule.forRoot(routes),
    HeaderComponent,
    SidebarComponent,
    App // Import standalone component directly
  ],
  providers: [],
  bootstrap: [App]
})
export class AppModule { }
