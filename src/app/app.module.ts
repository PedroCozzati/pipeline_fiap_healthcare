import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';

import { App } from './app';
import { routes } from './app.routes';
import { HeaderComponent } from './features/header-component/header.component';
import { SidebarComponent } from './features/sidebar-component/sidebar.component';

@NgModule({
  declarations: [ // Remove standalone components from declarations
  ], 
  imports: [
    BrowserModule,
    RouterModule.forRoot(routes),
    HeaderComponent, // Standalone component
    SidebarComponent, // Standalone component
    App // Import standalone component directly
  ],
  providers: [],
  bootstrap: [App]
})
export class AppModule { }
